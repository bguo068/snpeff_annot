#! /usr/bin/env python3

# %%
import argparse
import sys
from io import BytesIO
from pathlib import Path
from subprocess import check_output, run

import pandas as pd

from makedb import check_if_genome_exist, genome_name


def run_snpeff(
    in_vcf: str = "./tests/biallelic_ex.vcf.gz",
    out_vcf: str = "tmp.vcf.gz",
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
):
    genome = genome_name(version, species, strain)
    out_stat = Path(out_vcf.removesuffix(".vcf.gz") + "_stat.html")
    out_gene = Path(out_vcf.removesuffix(".vcf.gz") + "_stat.genes.txt")

    cmd = f"""
        set -eo pipefail
        snpEff -noDownload -ud 0 {genome} {in_vcf} -s {out_stat} -o gatk | bgzip -c > {out_vcf}
        bcftools index -f {out_vcf}
    """
    # print(cmd)
    run(cmd, shell=True, check=True, executable="/bin/bash")

    # remove unwanted files
    if out_stat.exists():
        out_stat.unlink()

    if out_gene.exists():
        out_gene.unlink()

    print(f"write_file: {out_vcf}")


# %%
def parse_annotation(out_vcf: str):

    # ------------ parse info for table content -----------
    bytes = check_output(
        f"""
        bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%INFO/EFF\n' {out_vcf}                     
    """,
        shell=True,
    )
    names = ["Chromosome", "Position", "Ref", "Alt", "EFF"]
    df_raw = pd.read_csv(BytesIO(bytes), sep="\t", names=names)

    df_eff = (
        df_raw.EFF.str.replace(r"\[.*\]", "", regex=True)
        .str.replace(r"\).*$", "", regex=True)
        .str.replace(r"\(", "", regex=True)
        .str.split("|", expand=True)
    )

    # ------------ parse info for table header  -----------

    cols = (
        check_output(
            f"""
        bcftools view -h {out_vcf} | grep -o 'Effect (.*)' | sed 's:Effect (::;s:\\[.*\\]::;s/ //g;s:)::' | tr '(' '|'
            """,
            shell=True,
            text=True,
        )
        .strip()
        .split("|")
    )

    # add header to table
    df_eff.columns = cols

    # everything together
    df_annot = pd.concat([df_raw.drop("EFF", axis=1), df_eff], axis=1)

    annot_file = out_vcf.removesuffix(".vcf.gz") + "_pretty_table.tsv"

    df_annot.to_csv(annot_file, sep="\t", index=False)
    print(f"write file: {annot_file}")

    return df_annot


def subset_by_gene_list(
    out_vcf: str = "./tmp.vcf.gz",
    out_annot: str | None = None,
    subset_by_gene_list: str = "./genes.csv",
):
    if out_annot is None:
        out_annot = out_vcf.removesuffix(".vcf.gz") + "_pretty_table.tsv"
    out_vcf_subset = out_vcf.removesuffix(".vcf.gz") + "_subset.vcf.gz"
    out_annot_subset = out_vcf.removesuffix(".vcf.gz") + "_pretty_table_subset.tsv"
    out_site_subset = out_vcf.removesuffix(".vcf.gz") + "_site_subset.tsv"
    df_subset = pd.read_csv(subset_by_gene_list, names=["Label", "Gene_Name"])

    df_annot = pd.read_csv(out_annot, sep="\t")
    df_annot_sel = df_annot[lambda df: df.Gene_Name.isin(df_subset.Gene_Name)]
    df_annot_sel.to_csv(out_annot_subset, sep="\t", index=False)

    # write a temp two-columsn list of sites
    df_annot_sel[["Chromosome", "Position"]].to_csv(
        out_site_subset, sep="\t", index=False, header=False
    )

    run(
        f""" bcftools view -R {out_site_subset} {out_vcf} -Oz -o {out_vcf_subset} """,
        shell=True,
        check=True,
    )
    print(f"write file: {out_vcf_subset}")
    print(f"write file: {out_annot_subset}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Annotate a VCF with snpEff and export the annotations as a TSV table",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--in_vcf", type=str, required=True, help="path to input vcf.gz files"
    )
    parser.add_argument(
        "--out_vcf", type=str, default="tmp.vcf.gz", help="path to output vcf.gz"
    )
    parser.add_argument(
        "--genome_version", type=int, default=44, help="genome version (plasmodb)"
    )
    parser.add_argument(
        "--genome_species",
        type=str,
        default="Pfalciparum",
        help="genome species (plasmodb)",
    )
    parser.add_argument(
        "--genome_strain", type=str, default="3D7", help="strain (plasmodb)"
    )
    parser.add_argument(
        "--subset_by_gene_list",
        type=str,
        default=None,
        help="file to two column file, comma-separated table which 2nd column indicating gene id ",
    )

    args = parser.parse_args()
    version = args.genome_version
    species = args.genome_species
    strain = args.genome_strain

    if not check_if_genome_exist(version, species, strain):
        print(
            f"Error: snpEff db {genome_name(version, species, strain)} not found;"
            " build it first with makedb.py (pixi run setup)",
            file=sys.stderr,
        )
        sys.exit(-1)

    run_snpeff(args.in_vcf, args.out_vcf, version, species, strain)

    parse_annotation(args.out_vcf)

    if args.subset_by_gene_list:
        subset_by_gene_list(args.out_vcf, None, args.subset_by_gene_list)
