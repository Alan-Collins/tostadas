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
        fasta

    main:
        // run vadr processes
        VADR (
            fasta,
            params.vadr_models_dir
        )

        VADR_POST_CLEANUP (
            VADR.out.vadr_outputs,
            params.meta_path,
            fasta
        )
    
    emit:
        gff = VADR_POST_CLEANUP.out.gff
}

