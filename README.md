# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

For the complete TOSTADAS documentation, please see the [Wiki](https://github.com/CDCgov/tostadas/wiki)

## Overview
**T O S T A D A S**  
**T**oolkit for **O**pen **S**equence **T**riage, **A**nnotation, and **DA**tabase **S**ubmission  
  
A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories.  Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing:  

+ Metadata Validation   
+ Genome Annotation    
+ File submission    

The current release is tested with sequence data from Poxviruses and select bacteria but TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both.

## Quick Start
❗ Note: If you are a CDC user, please follow the set-up instructions found here: [CDC User Guide](https://github.com/CDCgov/tostadas/wiki/CDC-User-Guide)

### 1. Clone the repository to your local machine
```
git clone https://github.com/CDCgov/tostadas.git
```
### 2. Install mamba and add it to your PATH 

 **2a. Install mamba** 
 
❗ Note: If you have mamba installed in your local environment, skip ahead to step 3 ([Create and activate a conda environment](https://github.com/CDCgov/tostadas/edit/dev/README.md#3-create-and-activate-a-conda-environment))
```
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```
 **2b. Add mamba to PATH:**
```
export PATH="$HOME/mambaforge/bin:$PATH"
```
### 3. Create and activate a conda environment

 **3a. Create an empty conda environment**
```
conda create --name tostadas
```
This conda environment will be used to install Nextflow.

 **3b. Activate the environment**
```
conda activate tostadas
```
Verify which environment is active by running the following conda command: `conda env list`. The active environment will be denoted with an asterisk *

### 4. Install Nextflow using mamba and the bioconda Channel
```
mamba install -c bioconda nextflow
```
### 5. Update the default submissions config file with your NCBI username and password, and run the following nextflow command to execute the scripts with default parameters and the local run environment: 
```
# update this config file (you don't have to use vim)
vim bin/config_files/default_config.yaml
# test command for virus reads
nextflow run main.nf -profile test,<singularity|docker|conda> --virus
```
The pipeline outputs appear in `tostadas/test_output`

### 6. Start running your own analysis

**Annotate and submit viral reads**
```
nextflow run main.nf -profile docker --virus --fasta_path <path/to/fasta/files> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --output_dir <path/to/output/dir/>
```
**Annotate and submit bacterial reads**
```
nextflow run main.nf -profile docker --bacteria --fasta_path <path/to/fasta/files> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light/full> --output_dir <path/to/output/dir/>
```
Refer to the wiki for more information on input parameters and use cases

## Get in Touch
If you need to report a bug, suggest new features, or just say “thanks”, [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and we’ll try to get back to you as soon as possible!

## Acknowledgements
### Contributors
Kyle O'Connell | Yesh Kulasekarapandian | Ankush Gupta | Cole Tindall | Jessica Rowell | Swarnali Louha | Michael Desch | Ethan Hetrick | Nick Johnson | Kristen Knipe | Shatavia Morrison | Yuanyuan Wang | Michael Weigand | Dhwani Batra | Jason Caravas | Lynsey Kovar | Hunter Seabolt | Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva | Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth

### Tools
The submission portion of this pipeline was adapted from SeqSender. To find more information on this tool, please refer to their GitHub page: [SeqSender](https://github.com/CDCgov/seqsender)

## Resources

:link: NCBI Submission Guidelines: https://submit.ncbi.nlm.nih.gov/sarscov2/sra/#step6

:link: SeqSender Documentation: https://github.com/CDCgov/seqsender

:link: Liftoff Documentation: https://github.com/agshumate/Liftoff

:link: VADR Documentation:  https://github.com/ncbi/vadr.git

:link: Bakta Documentation:  https://github.com/oschwengers/bakta

:link: RepeatMasker Documentation: https://www.repeatmasker.org/

