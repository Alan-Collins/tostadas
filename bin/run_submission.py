#!/usr/bin/env python3

import argparse
import os
import glob
import subprocess
import yaml

def get_args():
    """ All potential arguments passed in through command line
    """ 
    parser = argparse.ArgumentParser()
    parser.add_argument("--validated_meta_path", type=str, help='Path to the metadata directory containing validated meta files ending with .tsv')
    parser.add_argument("--lifted_fasta_path", type=str, help='Path to the fasta directory containing split fasta files ending with .fasta')
    parser.add_argument("--lifted_gff_path", type=str, help='Path to the gff directory containing reformatted gff files ending with .gff')
    parser.add_argument("--config", type=str, help='Name of the config file')
    parser.add_argument("--unique_name", type=str, help='Name of batch')
    parser.add_argument("--prod_or_test", type=str, help='Whether it is a production or test submission')
    parser.add_argument("--submission_database", type=str, help='Which database to submit to')
    parser.add_argument("--req_col_config", type=str, help='Path to the required columns yamls')
    parser.add_argument("--update", type=str, help='Whether to update or not')
    return parser

class SubmitToDatabase:
    """ Class constructor containing methods and attributes associated with initial submission and update submission
    """
    def __init__(self):
        # get the arguments from argparse
        args = get_args().parse_args()
        self.parameters = vars(args)

    def main(self):
        """ Main function for calling the two different cases: (1) initial submission or (2) update submission
        """
        # either call initial submission or update submission
        if self.parameters['update'].lower() == 'false':
            self.initial_submission()
        elif self.parameters['update'].lower() == 'true':
            self.update_submission()

    def initial_submission(self):
        """ Function for initial submission
        """
        # make the dir for storing the command + terminal output
        sample_name = self.parameters['validated_meta_path'].split('/')[-1].split('.')[0]
        unique_dir_name = f"{self.parameters['unique_name']}.{sample_name}"
        os.makedirs(unique_dir_name)

        # get the command that will be used 
        command = f"submission.py --command {self.parameters['submission_database']} --unique_name {self.parameters['unique_name']} --fasta {self.parameters['lifted_fasta_path']} \
                  --metadata {self.parameters['validated_meta_path']} --gff {self.parameters['lifted_gff_path']} --config {self.parameters['config']} --test_or_prod {self.parameters['prod_or_test']} \
                  --req_col_config {self.parameters['req_col_config']}"

        # open a txt file and write the command 
        with open(f"{unique_dir_name}/{sample_name}_initial_submit_info", "w") as f:
            f.write(f"ACTUAL COMMAND USED: {command}\n")
        f.close()

        # submit the submission.py job as a subprocess + write the terminal output
        file_ = open(f"{unique_dir_name}/{sample_name}_initial_terminal_output.txt", "w+")
        subprocess.run(command, shell=True, stdout=file_)
        file_.close()


    def update_submission(self):
        """ Calls update submission
        """
        if not os.path.isabs(self.parameters['nf_output_dir']):
            self.parameters['nf_output_dir'] = f"{self.parameters['launch_dir']}/{self.parameters['nf_output_dir']}"

        if not os.path.isabs(self.parameters['submission_output_dir']):
            terminal_dir = f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/terminal_outputs",
            command_dir = f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/commands_used"
        else:
            terminal_dir = f"{self.parameters['submission_output_dir']}/terminal_outputs", 
            command_dir = f"{self.parameters['submission_output_dir']}/commands_used"

        with open(f"{command_dir}/submit_info_for_update.txt", 'w') as f:
            f.write(f"ACTUAL COMMAND USED: python {self.parameters['submission_script']} update_submissions\n")
            f.close()

        os.system(f"python {self.parameters['submission_script']} update_submissions")
        """
        with open(f"{terminal_dir}/test.txt", "w+") as f:
            subprocess.run(f"python {self.parameters['submission_script']} update_submissions", shell=true, stdout=f)
        f.close()
        """

if __name__ == "__main__":
    submit_to_database = SubmitToDatabase()
    submit_to_database.main()
