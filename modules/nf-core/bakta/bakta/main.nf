/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    // label 'bakta'
    
    conda (params.enable_conda ? "bioconda::bakta==1.9.1" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.1--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.1--pyhdfd78af_0' }"
    
    publishDir "$params.output_dir/$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output
    
    input:
    val signal
    path db_path
    tuple val(meta), path(fasta_path)

    script:
    def args = task.ext.args  ?: ''
    """
    bakta --db $db_path  \
        --min-contig-length $params.bakta_min_contig_length \
        --prefix ${fasta_path.getSimpleName()} \
        --output ${fasta_path.getSimpleName()} \
        --threads $params.bakta_threads \
        --genus $params.bakta_genus \
        --species $params.bakta_species \
        --strain $params.bakta_strain 
        --compliant \
        --plasmid $params.bakta_plasmid  \
        --locus $params.bakta_locus \
        --locus-tag $params.bakta_locus_tag \
        --translation-table $params.bakta_translation_table \
        --complete $params.complete \
        --meta $params.meta \
        --complete $params.complete \
        --meta $params.meta \
        --keep_contig_headers $params.keep_contig_headers \
        --version $params.version \
        --verbose $params.verbose \
        --debug $params.debug \
        --skip_trna $params.skip_trna \
        --skip_tmrna $params.skip_tmrna \
        --skip_rrna $params.skip_rrna \
        --skip_ncrna $params.skip_ncrna \
        --skip_ncrna_region $params.skip_ncrna_region \
        --skip_crispr $params.skip_crispr \
        --skip_cds $params.skip_cds \
        --skip_pseudo $params.skip_pseudo \
        --skip_sorf $params.skip_sorf \
        --skip_gap $params.skip_gap \
        --skip_ori $params.skip_ori \
        --skip_plot $params.skip_plot \
        --bakta_min_contig_length $params.bakta_min_contig_length \
        --bakta_genus $params.bakta_genus \
        --bakta_species $params.bakta_species \
        --bakta_strain $params.bakta_strain \
        --bakta_plasmid $params.bakta_plasmid \
        --bakta_locus $params.bakta_locus \
        --bakta_locus_tag $params.bakta_locus_tag \
        --bakta_translation_table $params.bakta_translation_table \
        $fasta_path
    """
    
    output:
    path "${fasta_path.getSimpleName()}/*.fna",   emit: fna
    path "${fasta_path.getSimpleName()}/*.gff3",   emit: gff3
    path "${fasta_path.getSimpleName()}/*.faa",   emit: faa
    path "${fasta_path.getSimpleName()}/*.embl",   emit: embl
    path "${fasta_path.getSimpleName()}/*.ffn",   emit: ffn
    path "${fasta_path.getSimpleName()}/*.gbff",   emit: gbff
    path "${fasta_path.getSimpleName()}/*.json",   emit: json
    path "${fasta_path.getSimpleName()}/*.log",   emit: log
    path "${fasta_path.getSimpleName()}/*.png",   emit: png
    path "${fasta_path.getSimpleName()}/*.svg",   emit: svg
    path "${fasta_path.getSimpleName()}/*.tsv",   emit: tsv
    path "${fasta_path.getSimpleName()}/*.txt",   emit: txt
}