/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION_FULL {

    // define the command line arguments based on the value of params.submission_test_or_prod
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    //label'main'

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'cdcgov/seqsender-dev:latest' : 'cdcgov/seqsender-dev:latest' }"

    input:
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(annotations_path)
    path(fastq_dir)
    path submission_config
    path req_col_config
    val annotation_name

    script:
    """     
    ln -s $fastq_dir raw_reads

    submission.py submit --genbank --sra --biosample --organism $params.organism \
                         --submission_dir .  --submission_name ${validated_meta_path.getBaseName()} --config $submission_config  \
                         --metadata_file $validated_meta_path --fasta_file $fasta_path --gff_file $annotations_path --table2asn $test_flag
    """

    output:
    path "$params.batch_name.${validated_meta_path.getBaseName()}", emit: submission_files 
}