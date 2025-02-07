### 1. Log into the server
In a terminal, run `ssh [your_name]@arthas.igs.umaryland.edu` to log onto the server;
Then use launch an interactive session: 
```sh
module load slurm
srun -n 2 --mem 10G --pty bash
```

### 2. Activate the shared conda environment
After you enter the interactive session, run
```sh
eval "$(/local/projects-t2/CVD/Takala-Harrison/AFRIMS/miniconda3/bin/conda shell.bash hook)" 
export PATH=$PATH:/local/projects-t2/CVD/Takala-Harrison/AFRIMS/SnpEff
conda activate snpeff
```
### 3. Prepare your VCF file
For better post-processing of the annotated vcf file, 
it is recommended to convert the multi-allelic site to biallelic sites, for example:

`bcftools norm -m -any input.vcf.gz | bcftools view -q 0.001:minor -Oz -o input_norm.vcf.gz`

If your file is already biallelic, you can skip this step.

### 4. Annotate your VCF file

Run the annotating script:
```sh
annotate.py --vcf [your].vcf.gz --out_prefix annotated --genes [genes.tsv] 
```

#### Example files
1. A `VCF` file containing samples collected in 2015 or after can be found here:
`/local/projects-t2/CVD/Takala-Harrison/AFRIMS/SnpEff/VCFs/afrims_2015_or_newer_biallelic_maf0_001.vcf.gz`

2. An example `genes.tsv` file can be found here:
`/local/projects-t2/CVD/Takala-Harrison/AFRIMS/SnpEff/genes.csv`

3. Run the script with the provided examples
```sh
annotate.py --vcf /local/projects-t2/CVD/Takala-Harrison/AFRIMS/SnpEff/VCFs/afrims_2015_or_newer_biallelic_maf0_001.vcf.gz --out_prefix annotated --genes /local/projects-t2/CVD/Takala-Harrison/AFRIMS/SnpEff/genes.csv 
```



#### Find the Gene IDs for your genes

Go to [plasmoDb](https://plasmodb.org/plasmo/app/). Click 'My Organism Preference' to choose "k13"
Plasmodium falciparum 3D7" and then click apply.

<img src="https://user-images.githubusercontent.com/13037898/169898489-b5f71c2d-046d-49cb-abd6-4e5b0e073d04.png" width="600" />

Then in the search bar, you could search the gene id by name, such k13

### 5. Download the result files
Several files will be created. The most relevant one is: `XXXX_genotypes_filt.tsv`
1. On the server, you can get the full path of your file: `realpath *genotypes_filt.tsv`. 
Copy the full path to your clipboard (using the mouse) and you will need it in the next step.
2. On your local machine, open a new terminal window and 
use scp to download your file: `scp [your_name]@arthas.igs.umaryland.edu:/full/path/to/your/file ./`
3. You could your `Excel` or `libreoffice` to open the downloaded file.
