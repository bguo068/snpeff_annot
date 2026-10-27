#! /usr/bin/env python3

# %%
import argparse
import os
import shutil
import sys
from pathlib import Path
from subprocess import run


def genome_name(
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
) -> str:
    return f"PlasmoDB-{version}_{species}{strain}"


def get_snpeff_root() -> Path:
    exe = shutil.which("snpEff")
    assert exe, "snpEff command cannot be found"
    return Path(exe).absolute().resolve().parent


def list_snpeff_db() -> list[str]:
    snpeff_root = get_snpeff_root()
    return [p.parent.name for p in (snpeff_root / "data").glob("*/sequences.fa")]


def check_if_genome_exist(
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
):
    return genome_name(version, species, strain) in list_snpeff_db()


def create_snpeff_db(
    ref_dir="ref",
    version: int = 44,
    species: str = "Pfalciparum",
    strain: str = "3D7",
):
    # define genome
    genome = genome_name(version, species, strain)
    ref_dir = Path(ref_dir).absolute()

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
    seq = [
        f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_Genome.fasta",
        f"{target_dir}/sequences.fa",
    ]
    gene = [
        f"{ref_dir}/PlasmoDB-{version}_{species}{strain}.gff",
        f"{target_dir}/genes.gff",
    ]
    cds = [
        f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_AnnotatedCDSs.fasta",
        f"{target_dir}/cds.fa",
    ]
    prot = [
        f"{ref_dir}/PlasmoDB-{version}_{species}{strain}_AnnotatedProteins.fasta",
        f"{target_dir}/protein.fa.orig",
    ]
    for src, dst in [seq, gene, cds, prot]:
        if not Path(src).exists() and (
            run(
                f"""
                    set -xoueE pipefail
                    mkdir -p {ref_dir}/archive
                    cd {ref_dir}/archive
                    [ -s {genome}.tgz ] || wget https://github.com/bguo068/snpeff_annot/releases/download/v26.09.14-alpha/{genome}.tgz
                    cd {ref_dir}
                    tar xf archive/{genome}.tgz
                    """,
                shell=True,
                capture_output=True,
                check=False,
            ).returncode
            != 0
            or not Path(src).exists()
        ):
            print(
                f"\n\nError: {src} not found. You need to down it from plasmodb",
                file=sys.stderr,
            )
            sys.exit(-1)
        shutil.copy2(src, dst)

    ## fix header in protein.fa
    #   1) change separator from | to space
    #   2) remove the '-p1' suffix in protein id and make it consistent with
    #   cds transcript ids
    run(
        f"""
        sed -e 's/ | / /g;s/-p[0-9]* / /' {target_dir}/protein.fa.orig >  \
{target_dir}/protein.fa
        rm -rf {target_dir}/protein.fa.orig
    """,
        shell=True,
        check=True,
    )

    # build the db
    res = run(
        f"snpEff build -gff3 -v {genome}",
        shell=True,
        check=False,
        capture_output=True,
    )
    if res.returncode != 0:
        print(res.stderr)
        sys.exit(-2)
    print(f"created db: {genome}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the snpEff database of a PlasmoDB genome, if missing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        "--ref_dir",
        type=str,
        default=None,
        help="reference folder used to find files for making snpEff database",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="rebuild the database even if it already exists",
    )

    args = parser.parse_args()
    version = args.genome_version
    species = args.genome_species
    strain = args.genome_strain
    ref_dir = args.ref_dir
    if ref_dir is None:
        pixi_toml_path = os.getenv("PIXI_PROJECT_MANIFEST")
        if pixi_toml_path is None:
            pixi_toml_path = "."
        ref_dir = Path(pixi_toml_path).parent / "ref"

    if args.force or not check_if_genome_exist(version, species, strain):
        create_snpeff_db(ref_dir, version, species, strain)
    else:
        print(f"db exists: {genome_name(version, species, strain)}")
