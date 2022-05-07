# /usr/bin/env python3

import pandas as pd
from subprocess import run
from pathlib import Path
import argparse
import allel
import re

parser = argparse.ArgumentParser()
parser.add_argument('--vcf', type=str, required=True)
parser.add_argument('--genome', type=str, required='PlasmoDB-44_Pfalciparum3D7')
parser.add_argument('--out_prefix', type=str, default='out')

args = parser.parse_args()
vcf = args.vcf
genome = args.genome
out_prefix = args.out_prefix
out_vcf = f'{out_prefix}.vcf.gz'
out_stats = f'{out_prefix}_stats.html'
out_table = f'{out_prefix}.tsv'


# --- ----------run annotation -------------------------------
cmd = f""" snpEff -ud 0 {genome} {vcf} -s {out_stats} -o gatk | bgzip -c > {out_vcf} """
print(cmd)
run(cmd, shell=True)

# -------------- parser annotation -------------------------------
# TODO: need to convert multi-allele site to biallelic sites
calldata = allel.read_vcf(out_vcf, fields=['CHROM', 'POS', 'REF', 'ALT', 'variants/EFF'], alt_number=1)

# extract header
eff_header = [l for l in allel.read_vcf_headers(out_vcf).headers if 'EFF' in l][0]
eff_header = re.split("'", eff_header)[1]
eff_header = re.split('\[', eff_header)[0]
eff_header = eff_header.replace('(', '|').replace(' ', '').replace('|', '\t').split()
eff_header

# extract annotation fileds
eff_df = pd.Series(calldata['variants/EFF']).str.replace('(', '|').str.replace(')', '').str.split('|', expand=True)
eff_df = eff_df.iloc[:, :(len(eff_header))] # remove the last two optional columns, error/warnings
eff_df.columns = eff_header

# variant info
variants_df = pd.DataFrame({
    'Chrom': calldata['variants/CHROM'],
    'POS': calldata['variants/POS'],
    'REF': calldata['variants/REF'],
    'ALT': calldata['variants/ALT']
})

# combined table
res_df = pd.concat([variants_df, eff_df], axis=1)
res_df.to_csv(out_table, sep='\t', index=None)