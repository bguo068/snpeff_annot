## Activate conda environment

```sh
eval "$(/local/data/Malaria/Projects/Takala-Harrison/AFRIMS/miniconda3/bin/conda shell.bash hook)" 
conda activate snpeff
```

## Prepare Vcf file

For better post-processing of the annotated vcf file, it is recommended to convert 
the multi-allelic site to biallelic sites, for example 

```
bcftools norm -m -any input.vcf.gz -Oz -o input_norm.vcf.gz
```


## Run the annotating script

```sh
./annotate.py --vcf [your].vcf.gz --out_prefix out
```
