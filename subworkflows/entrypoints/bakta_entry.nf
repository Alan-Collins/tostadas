#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY SPLIT FASTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA                                                 } from "../../modules/bakta_annotation/main"
include { BAKTA_POST_CLEANUP                                    } from "../../modules/post_bakta_annotation/main"

workflow RUN_BAKTA {

    main:
        // run bakta annotation on single fasta files
        BAKTA (
            'dummy utility signal',
              params.db_path,
              params.fasta_path
        )
	BAKTA_POST_CLEANUP (
	     BAKTA.out.bakta_results,
	     params.meta_path,
	     params.fasta_path
	)
}


