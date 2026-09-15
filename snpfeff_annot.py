# %%
import argparse
import shutil
import sys
from io import BytesIO
import os
from pathlib import Path
from subprocess import check_output, run

import pandas as pd


def get_snpeff_root()-> Path:
    exe =  shutil.which("snpEff")
    assert exe, "snpEff command cannot be found"
    return Path(exe).absolute().resolve().parent

def list_snpeff_db()-> list[str]:
    snpeff_root = get_snpeff_root()
    return [p.parent.name for p in (snpeff_root / "data").glob("*/sequences.fa")]

def check_if_genome_exist(
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
):
    genome = f"PlasmoDB-{version}_{species}{strain}"
    return genome in list_snpeff_db()

def create_snpeff_db(
    ref_dir="ref",
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
):
    # define genome
    genome = f"PlasmoDB-{version}_{species}{strain}"

    # define paths
    snpeff_root = get_snpeff_root()
    conf_path = snpeff_root / "snpEff.config"
    target_dir = snpeff_root / "data" / genome
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(exist_ok=True, parents=True)


    # update if config file if needed
    conf_line = f"{genome}.genome :  {species}{strain}"
    if conf_line not in conf_path.read_text():
        with open(conf_path, "at") as f:
            f.writelines([f"{conf_line}\n"])

    # copy and fix files
    seq=[f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_Genome.fasta",f"{target_dir}/sequences.fa"]
    gene = [f"{ref_dir}/PlasmoDB-{version}_{species}{strain}.gff",f"{target_dir}/genes.gff"]
    cds = [f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_AnnotatedCDSs.fasta",f"{target_dir}/cds.fa"]
    prot = [f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_AnnotatedProteins.fasta",f"{target_dir}/protein.fa.orig"]
    for (src, dst) in [seq, gene, cds, prot]:
        if not Path(src).exists():
            try:
                run(f"""
                    cd {ref_dir}
                    tar xf archive/{genome}.tgz
                    """, shell=True, check=True)
            except:  # noqa: E722
                print("\n\nError: {src} not found. You need to down it from plasmodb", file = sys.stderr)
                sys.exit(-1)
        shutil.copy2(src, dst)

    ## fix header in protein.fa 
    #   1) change separator from | to space 
    #   2) remove the '-p1' suffix in protein id and make it consistent with 
    #   cds transcript ids
    run(f'''
        sed -e 's/ | / /g;s/-p[0-9]* / /' {target_dir}/protein.fa.orig >  \
{target_dir}/protein.fa
        rm -rf {target_dir}/protein.fa.orig
    ''', shell=True, check=True)

    # build the db
    res =  run(
        f"snpEff build -gff3 -v PlasmoDB-{version}_{species}{strain}",
        shell=True, check=False, capture_output=True
    )
    if res.returncode!=0:
        print(res.stderr)
        sys.exit(-2)
    print(f"created db: {genome}")

def run_snpeff(
    in_vcf: str="./tests/biallelic_ex.vcf.gz",
    out_vcf: str = "tmp.vcf.gz",
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",

):
    genome = f"PlasmoDB-{version}_{species}{strain}"
    out_stat = out_vcf.removesuffix("vcf.gz") + "_stat.hmlt"

    cmd = f""" snpEff -noDownload -ud 0 {genome} {in_vcf} -s {out_stat} -o gatk | bgzip -c > {out_vcf} """
    # print(cmd)
    run(cmd, shell=True, check=True)

    print("write_file: out_vcf")


# %%
def parse_annotation(out_vcf:str):

    # ------------ parse info for table content -----------
    bytes =  check_output(f"""
        bcftools query -f '%CHROM\t%POS\t%REF\t%ALT\t%INFO/EFF\n' {out_vcf}                     
    """, shell=True,)
    names = ['Chromosome', 'Position', 'Ref', 'Alt', 'EFF']
    df_raw =  pd.read_csv( BytesIO(bytes),sep='\t', names=names )

    df_eff =  df_raw.EFF.str.replace(r"\[.*\]", "", regex=True).str.replace(
        r"\).*$", "", regex=True
    ).str.replace(r"\(", "", regex=True).str.split("|", expand=True)

    # ------------ parse info for table header  -----------
    
    cols =  check_output(f"""
        bcftools view -h {out_vcf} | grep -o 'Effect (.*)' | sed 's:Effect (::;s:\\[.*\\]::;s/ //g;s:)::' | tr '(' '|'
            """, shell=True, text=True).strip().split("|")

    # add header to table
    df_eff.columns = cols

    # everything together
    df_annot = pd.concat([df_raw.drop("EFF", axis=1), df_eff], axis=1)

    annot_file = out_vcf.removesuffix("vcf.gz") + "_pretty_table.tsv"

    df_annot.to_csv(annot_file, sep='\t', index=False)
    print(f"write file: {annot_file}")

    return df_annot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_vcf", type=str, default="./tests/biallelic_ex.vcf.gz")
    parser.add_argument("--out_vcf", type=str, default="tmp.vcf.gz")
    parser.add_argument("--genome_version", type=int, default=44)
    parser.add_argument("--genome_species", type=str, default="Pfalciparum")
    parser.add_argument("--genome_strain", type=str, default="3D7")
    parser.add_argument("--ref_dir", type=str, default=None)

    args = parser.parse_args()
    version = args.genome_version
    species = args.genome_species
    strain = args.genome_strain
    ref_dir = args.ref_dir
    if ref_dir is None:
        pixi_toml_path =os.getenv("PIXI_PROJECT_MANIFEST") 
        if pixi_toml_path is None:
            pixi_toml_path = '.'
        ref_dir = Path(pixi_toml_path) / "ref"

    if not check_if_genome_exist(version, species, strain):
        create_snpeff_db(ref_dir, version, species, strain)


    run_snpeff(
        args.in_vcf, args.out_vcf, version, species, strain
    )

    parse_annotation(args.out_vcf)
