/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION_GENBANK {

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    //label'main'

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(annotations_path)
    path submission_config
    path req_col_config
    val annotation_name

    script:
    """
    submission.py submit --genbank $params.genbank --biosample $params.biosample --organism $params.organism \
                         --submission_dir ${task.workDir}  --submission_name ${validated_meta_path.getBaseName()} --config $submission_config  \
                         --validated_meta_path $validated_meta_path --fasta_path $fasta_path --gff_path $annotations_path --table2asn true \
                         --prod_or_test $params.submission_prod_or_test --req_col_config $req_col_config --update false --send_submission_email $params.send_submission_email
    """

    output:
    path "$params.batch_name.${validated_meta_path.getBaseName()}", emit: submission_files 
}