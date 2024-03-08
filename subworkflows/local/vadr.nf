#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            VADR SUBWORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VADR                                              } from "../../modules/local/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../../modules/local/post_vadr_annotation/main"


workflow RUN_VADR {
    take:
        fasta_files

    main:
        // run vadr processes
        VADR (
            fasta_files,
            params.vadr_models_dir
        )

        VADR_POST_CLEANUP (
            VADR.out.vadr_outputs,
            params.meta_path,
            fasta_files
        )
    
    emit:
        gff = VADR_POST_CLEANUP.out.gff
}

