/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST VADR CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_POST_CLEANUP {
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    path vadr_outputs
    tuple val(meta), path (meta_path)
	tuple val(meta), path(fasta_path)
    
    output:
    path('*.gff') , emit: gff
    path('*.txt'), emit: errors
    path('*.tbl'), emit: tbl

    script:
    """
    post_vadr_cleanup.py \
        --meta_path $meta_path \
        --vadr_outdir $vadr_outputs \
        --vadr_outputs $vadr_outputs
    """
}