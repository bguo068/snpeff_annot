# snpeff_annot

Annotate a VCF file with [snpEff](https://pcingola.github.io/SnpEff/) using a
[PlasmoDB](https://plasmodb.org/) reference genome, and export the annotations to
a convenient TSV table.

`snpeff_annot.py` performs four steps:

1. Make sure the requested snpEff database exists, building it from local
   PlasmoDB reference files if needed.
2. Run snpEff on the input VCF (keeping it within the `gatk` output format) and
   index the result with `bcftools`.
3. Parse the `EFF` field of the annotated VCF into a readable table
   (`*_pretty_table.tsv`).
4. Optionally subset the sites to a list of genes of interest.

## Install pixi

See https://pixi.prefix.dev/latest/installation/

## Clone the GitHub repo

```sh
git clone https://github.com/bguo068/snpeff_annot
cd snpeff_annot
```

## Prepare your VCF file

For better post-processing of the annotated VCF file, it is recommended to
convert multi-allelic sites to biallelic sites, for example:

```sh
bcftools norm -m- input.vcf.gz -Oz -o input_norm.vcf.gz
```

If your file is already biallelic, you can skip this step.

## Annotate your VCF file

Run the annotating script:

```sh
pixi run snpeff_annot --in_vcf <your.vcf.gz> --out_vcf <annotated.vcf.gz>
```

A pixi task is also provided, so the same script can be run from outside the
project folder:

```sh
pixi run -m /path/to/snpeff_annot snpeff_annot --in_vcf <abs/path/your.vcf.gz> --out_vcf <abs/path/annotated.vcf.gz>
```

## Options

| Option | Default | Description |
| --- | --- | --- |
| `--in_vcf` | *(required)* | Path to the input `vcf.gz`. |
| `--out_vcf` | `tmp.vcf.gz` | Path to the annotated output `vcf.gz`. |
| `--genome_version` | `44` | PlasmoDB genome version. |
| `--genome_species` | `Pfalciparum` | PlasmoDB species. |
| `--genome_strain` | `3D7` | PlasmoDB strain. |
| `--subset_by_gene_list` | *(none)* | Two-column comma-separated table whose **second** column holds the gene IDs to subset to. |
| `--ref_dir` | the `ref/` folder next to `pixi.toml` | Reference folder used to find the files for building the snpEff database. |

The genome name is derived from the version/species/strain as
`PlasmoDB-{version}_{species}{strain}`, for example `PlasmoDB-44_Pfalciparum3D7`.

## snpEff database

On startup the script checks whether the genome database is already installed in
the snpEff `data` directory. If it is missing, the database is built
automatically:

- It adds a `<genome>.genome` line to `snpEff.config` if necessary.
- It looks for the PlasmoDB files in `--ref_dir` (default `ref/`):
  - `PlasmoDB-{version}_{species}{strain}_Genome.fasta`
  - `PlasmoDB-{version}_{species}{strain}.gff`
  - `PlasmoDB-{version}_{species}{strain}_AnnotatedCDSs.fasta`
  - `PlasmoDB-{version}_{species}{strain}_AnnotatedProteins.fasta`
- If a file is not present, it tries to extract
  `ref/archive/PlasmoDB-{version}_{species}{strain}.tgz`. Archives for versions
  44–71 are shipped in `ref/archive/`.
- Protein FASTA headers are reformatted so that the protein IDs match the CDS
  transcript IDs (separators `|` become spaces and the `-p1` suffix is removed).
- Finally it runs `snpEff build -gff3`.

If the files cannot be found in either location, user will need to download them from PlasmoDB and
place them in `ref/`.

## Output files

Given `--out_vcf annotated.vcf.gz`, the script writes:

| File | Description |
| --- | --- |
| `annotated.vcf.gz` (+ `.csi`) | Annotated, indexed VCF. |
| `annotated_pretty_table.tsv` | Annotation table parsed from the VCF `EFF` field. |

When `--subset_by_gene_list` is given, it additionally writes:

| File | Description |
| --- | --- |
| `annotated_subset.vcf.gz` | VCF restricted to sites in the gene list. |
| `annotated_pretty_table_subset.tsv` | Annotation table restricted to the gene list. |
| `annotated_site_subset.tsv` | Two-column (chromosome, position) list of the selected sites. |

The snpEff summary files (`*_stat.html`, `*_stat.genes.txt`) are removed after
the run.

## Example files

1. A `VCF` file: `tests/biallelic_ex.vcf.gz`.
2. An example gene list: `genes.csv`, a two-column (label, gene ID) CSV.
3. Run the script with the provided examples:

```sh
pixi run python ./snpeff_annot.py \
  --in_vcf tests/biallelic_ex.vcf.gz \
  --out_vcf out.vcf.gz \
  --genome_version 44 \
  --subset_by_gene_list genes.csv
```

This produces `out.vcf.gz`, `out_pretty_table.tsv`, `out_subset.vcf.gz`,
`out_pretty_table_subset.tsv`, and `out_site_subset.tsv`.

## Find the gene IDs for your genes

Go to [PlasmoDB](https://plasmodb.org/plasmo/app/). Click *My Organism
Preference* to choose "Plasmodium falciparum 3D7" and then click apply.

<img src="https://user-images.githubusercontent.com/13037898/169898489-b5f71c2d-046d-49cb-abd6-4e5b0e073d04.png" width="600" />

Then, in the search bar, you can search the gene ID by name, such as `k13`.
