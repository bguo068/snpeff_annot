# Activate conda environment

```sh
eval "$(/local/data/Malaria/Projects/Takala-Harrison/AFRIMS/miniconda3/bin/conda shell.bash hook)" 
conda activate snpeff
```

# Prepare Vcf file

For better post-processing of the annotated vcf file, it is recommended to convert 
the multi-allelic site to biallelic sites 


# Run the annotating script

```sh
/local/data/Malaria/Projects/Takala-Harrison/AFRIMS/SnpEff/annotate.py --vcf [your].vcf.gz --out_prefix out
```
