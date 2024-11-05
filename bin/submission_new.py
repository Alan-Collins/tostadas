#!/usr/bin/env python3

import os
import sys
from datetime import datetime
import argparse
import yaml
from lxml import etree
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom  # Import minidom for pretty-printing
import os
import math  # Required for isnan check
import csv
import time
import subprocess
import pandas as pd
from abc import ABC, abstractmethod
#import paramiko
import ftplib
from zipfile import ZipFile

def fetch_and_parse_report(submission_object, client, submission_id, submission_dir, output_dir, type):
    # Connect to the FTP/SFTP client
    client.connect()
    client.change_dir('submit')  # Change to 'submit' directory
    client.change_dir(submission_dir)  # Change to Test or Prod
    client.change_dir(f"{submission_id}_{type}")  # Change to sample-specific directory
    # Check if report.xml exists and download it
    report_file = "report.xml"
    if client.file_exists(report_file):
        print(f"Report found at {report_file}")
        report_local_path = os.path.join(output_dir, 'report.xml')
        client.download_file(report_file, report_local_path)
        # Parse the report.xml
        parsed_report = submission_object.parse_report_xml(report_local_path)
        # Save as CSV to top level sample submission folder
        # output_dir = 'path/to/results/sample_name/database' and we want to save a report for all samples to 'path/to/results/'
        report_filename = os.path.join(os.path.dirname(os.path.dirname(output_dir)), 'submission_report.csv')
        print(f"save_report_to_csv inputs are: {parsed_report}, {report_filename}")
        submission_object.save_report_to_csv(parsed_report, report_filename)
        return parsed_report
    else:
        print(f"No report found for submission {submission_id}")
        return None

def submission_main():
    """ Main for initiating submission steps
    """
    # Get all parameters from argparse
    parameters_class = GetParams()
    parameters = parameters_class.parameters

    # Get the submission config file dictionary
    config_parser = SubmissionConfigParser(parameters)
    config_dict = config_parser.load_config()
    
    # Read in metadata file
    metadata_df = pd.read_csv(parameters['metadata_file'], sep='\t')
    
    # Initialize the Sample object with parameters from argparse
    sample = Sample(
        sample_id=parameters['submission_name'],
        metadata_file=parameters['metadata_file'],
        fastq1=parameters.get('fastq1'),
        fastq2=parameters.get('fastq2'),
        fasta_file=parameters.get('fasta_file'),
        annotation_file=parameters.get('annotation_file')
    )
    # Perform file validation
    sample.validate_files()

    # Get list of all databases to submit to (or update)
    databases = [db for db in parameters if parameters[db] and db in ['biosample', 'sra', 'genbank', 'gisaid']]

    # Set the submission directory (test or prod)
    if parameters['test']:
        submission_dir = 'Test'
    else:
        submission_dir = 'Prod'

    # Prepare all submissions first (so files are generated even if submission step fails)
    if parameters['biosample']:
        biosample_submission = BiosampleSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/biosample", 
                                                   parameters['submission_mode'], submission_dir, 'biosample')
    if parameters['sra']:
        sra_submission = SRASubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/sra",
                                       parameters['submission_mode'], submission_dir, 'sra')
    if parameters['genbank']:
        genbank_submission = GenbankSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/genbank",
                                               parameters['submission_mode'], submission_dir, 'genbank')

    # If submission mode
    if parameters['submit']:
        # Submit all prepared submissions and fetch report once
        if parameters['biosample']:
            biosample_submission.submit()
        if parameters['sra']:
            sra_submission.submit()
        if parameters['genbank']:
            genbank_submission.submit()
            # Add more GB functions for table2asn submission and creating/emailing zip files

    # If update mode
    elif parameters['update']:
        start_time = time.time()
        timeout = 300  # 300 seconds (5 minutes)
        
        while time.time() - start_time < timeout:
            submission_objects = { 'biosample': biosample_submission, 'sra': sra_submission, 'genbank': genbank_submission }
            for db in databases:
                submission_object = submission_objects[db]
                result = submission_object.update_report()  # Call the fetch_report function repeatedly
                if result:  # If report fetch is successful, break the loop
                    print("Report successfully fetched")
                    break
                time.sleep(30)  # Wait before retrying
            else:
                print("Timeout occurred while trying to fetch the report")

class GetParams:
    """ Class constructor for getting all necessary parameters (input args from argparse and hard-coded ones)
    """
    def __init__(self):
        self.parameters = self.get_inputs()

    # read in parameters
    def get_inputs(self):
        """ Gets the user inputs from the argparse
        """
        args = self.get_args().parse_args()
        parameters = vars(args)
        return parameters

    @staticmethod
    def get_args():
        """ Expected args from user and default values associated with them
        """
        # initialize parser
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Automate the process of batch uploading consensus sequences and metadata to databases of your choices')
        # required parameters (do not have default)
        parser.add_argument("--submission_name", help='Name of the submission',	required=True)	
        parser.add_argument("--config_file", help="Name of the submission onfig file",	required=True)
        parser.add_argument("--metadata_file", help="Name of the validated metadata tsv file", required=True)
        parser.add_argument("--species", help="Type of organism data", required=True)
        parser.add_argument('--submit', action='store_true', help='Run the full submission process')
        parser.add_argument('--update', action='store_true', help='Run the update process to fetch and parse report')
        # optional parameters
        parser.add_argument("-o", "--output_dir", type=str, default='submission_outputs',
                            help="Output Directory for final Files, default is current directory")
        parser.add_argument("--test", help="Whether to perform a test submission.", required=False,	action="store_const", default=False, const=True)
        parser.add_argument("--fasta_file",	help="Fasta file to be submitted", required=False)
        parser.add_argument("--annotation_file", help="An annotation file to add to a Genbank submission", required=False)
        parser.add_argument("--fastq1", help="Fastq R1 file to be submitted", required=False)	
        parser.add_argument("--fastq2", help="Fastq R2 file to be submitted", required=False)
        parser.add_argument("--submission_mode", help="Whether to upload via ftp or sftp", required=False, default='ftp')	
        parser.add_argument("--genbank", help="Optional flag to run Genbank submission", action="store_const", default=False, const=True)
        parser.add_argument("--biosample", help="Optional flag to run BioSample submission", action="store_const", default=False, const=True)
        parser.add_argument("--sra", help="Optional flag to run SRA submission", action="store_const", default=False, const=True)
        parser.add_argument("--gisaid", help="Optional flag to run GISAID submission", action="store_const", default=False, const=True)
        return parser
    
class SubmissionConfigParser:
    """ Class constructor to read in config file as dict
    """
    def __init__(self, parameters):
        # Load submission configuration
        self.parameters = parameters
    def load_config(self):
        # Parse the config file (could be JSON, YAML, etc.)
        # Example: returns a dictionary with SFTP credentials, paths, etc.
        with open(self.parameters['config_file'], "r") as f:
            config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
        if type(config_dict) is dict:
            for k, v in config_dict.items():
                # If GISAID submission, check that GISAID keys have values
                if self.parameters["gisaid"]:
                    if k.startswith('GISAID') and not v:
                        print("Error: There are missing GISAID values in the config file.", file=sys.stderr)
                        sys.exit(1)					
                else:
                    # If NCBI submission, check that non-GISAID keys have values (note: this only check top-level keys)
                    if k.startswith('NCBI') and not v:
                        print("Error: There are missing NCBI values in the config file.", file=sys.stderr)
                        sys.exit(1)	
        else:	
            print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
            sys.exit(1)
        return config_dict

class Sample:
    def __init__(self, sample_id, metadata_file, fastq1, fastq2, fasta_file=None, annotation_file=None):
        self.sample_id = sample_id
        self.metadata_file = metadata_file
        self.fastq1 = fastq1
        self.fastq2 = fastq2
        self.fasta_file = fasta_file
        self.annotation_file = annotation_file
    # todo: add (or ignore) validation for cloud files 
    def validate_files(self):
        files_to_check = [self.metadata_file, self.fastq1, self.fastq2]
        if self.fasta_file:
            files_to_check.append(self.fasta_file)
        if self.annotation_file:
            files_to_check.append(self.annotation_file)
        missing_files = [f for f in files_to_check if not os.path.exists(f)]
        if missing_files:
            raise FileNotFoundError(f"Missing required files: {missing_files}")
        else:
            print(f"All required files for sample {self.sample_id} are present.")

class MetadataParser:
    def __init__(self, metadata_df):
        self.metadata_df = metadata_df
    # todo: will need to adjust these to handle custom metadata for whatever biosample pkg
    def extract_top_metadata(self):
        columns = ['sequence_name', 'title', 'description', 'authors', 'ncbi-bioproject', 'ncbi-spuid_namespace', 'ncbi-spuid']  # Main columns
        available_columns = [col for col in columns if col in self.metadata_df.columns]
        return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
    def extract_biosample_metadata(self):
        columns = ['bs_package','isolate','isolation_source','host_disease','host','collected_by','lat_lon',
                   'sex','age','geo_location','organism','purpose_of_sampling', 'race','ethnicity','sample_type']  # BioSample specific columns
        available_columns = [col for col in columns if col in self.metadata_df.columns]
        return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
    def extract_sra_metadata(self):
        columns = ['instrument_model','library_construction_protocol','library_layout','library_name','library_selection',
                   'library_source','library_strategy','nanopore_library_layout','nanopore_library_protocol','nanopore_library_selection',
                   'nanopore_library_source','nanopore_library_strategy','nanopore_sequencing_instrument']  # SRA specific columns
        available_columns = [col for col in columns if col in self.metadata_df.columns]
        return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
    def extract_genbank_metadata(self):
        columns = ['submitting_lab','submitting_lab_division','submitting_lab_address','publication_status','publication_title',
                    'assembly_protocol','assembly_method','mean_coverage']  # Genbank specific columns
        available_columns = [col for col in columns if col in self.metadata_df.columns]
        return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}

# todo: this opens an ftp connection for every submission; would be better I think to open it once every x submissions?
class Submission:
    def __init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type):
        self.sample = sample
        self.parameters = parameters
        self.submission_config = submission_config
        self.output_dir = output_dir
        self.submission_mode = submission_mode
        self.submission_dir = submission_dir
        self.type = type
        self.client = self.get_client()
    def get_client(self):
        if self.submission_mode == 'sftp':
            return SFTPClient(self.submission_config)
        elif self.submission_mode == 'ftp':
            return FTPClient(self.submission_config)
        else:
            raise ValueError("Invalid submission mode: must be 'sftp' or 'ftp'")
    def parse_report_xml(self, report_path):
        # Parse the XML file and extract required information
        tree = ET.parse(report_path)
        root = tree.getroot()
        report_dict = {
            'submission_name': self.sample.sample_id,
            'submission_type': self.type,
            'submission_status': None,
            'biosample_status': None,
            'biosample_accession': None,
            'biosample_message': None,
            'sra_status': None,
            'sra_accession': None,
            'sra_message': None,
            'genbank_status': None,
            'genbank_accession': None,
            'genbank_message': None,
            'genbank_release_date': None,
        }
        for action in root.findall('Action'):
            db = action.attrib.get('target_db')
            status = action.attrib.get('status')
            accession = action.attrib.get('accession')
            message = action.find('Message').text if action.find('Message') is not None else ""
            if db == 'biosample':
                report_dict['biosample_status'] = status
                report_dict['biosample_accession'] = accession
                report_dict['biosample_message'] = message
            elif db == 'sra':
                report_dict['sra_status'] = status
                report_dict['sra_accession'] = accession
                report_dict['sra_message'] = message
            elif db == 'genbank':
                report_dict['genbank_status'] = status
                if status == 'processed-ok':
                    # Handle Genbank-specific logic (AccessionReport.tsv)
                    accession_report = action.find('AccessionReport')
                    if accession_report is not None:
                        report_dict['genbank_accession'] = accession_report.find('Accession').text
                        report_dict['genbank_release_date'] = accession_report.find('ReleaseDate').text
                report_dict['genbank_message'] = message
        return report_dict
    def save_report_to_csv(self, report_dict, csv_file):
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=report_dict.keys())
            if not os.path.isfile(csv_file):
                writer.writeheader() # todo: need to use pandas to do this probably, not all keys are being written to the file 
            writer.writerow(report_dict)
        print(f"Submission report saved to {csv_file}")
    def submit_files(self, files, type):
        sample_subtype_dir = f'{self.sample.sample_id}_{type}' # samplename_<biosample,sra,genbank> (a unique submission dir)
        self.client.connect()
        self.client.change_dir('submit')  # Change to 'submit' directory
        self.client.change_dir(self.submission_dir) # Change to Test or Prod
        self.client.change_dir(sample_subtype_dir) # Change to unique dir for sample_destination
        for file_path in files:
            self.client.upload_file(file_path, f"{os.path.basename(file_path)}")
        print(f"Submitted files for sample {self.sample.sample_id}")
    def close(self):
        self.client.close()
    def fetch_report(self):
        fetch_and_parse_report(self, self.client, self.sample.sample_id, self.submission_dir, self.output_dir, self.type)

class SFTPClient:
    def __init__(self, config):
        self.host = config['NCBI_sftp_host']
        self.username = config['NCBI_username']
        self.password = config['NCBI_password']
        self.port = config.get('port', 22)
        self.sftp = None
        self.ssh = None
    def connect(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.username, password=self.password, port=self.port)
            self.sftp = self.ssh.open_sftp()
            print(f"Connected to SFTP: {self.host}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SFTP: {e}")
    def change_dir(self, dir_path):
        try:
            self.sftp.chdir(dir_path)  # Try to change to the directory
        except IOError:
            self.sftp.mkdir(dir_path)  # Create the directory if it doesn't exist
            self.sftp.chdir(dir_path)  # Change to the newly created directory
        print(f"Changed directories to {dir_path} ")
    def file_exists(self, file_path):
        try:
            self.sftp.stat(file_path)
            return True
        except IOError:
            return False
    def download_file(self, remote_path, local_path):
        try:
            self.sftp.get(remote_path, local_path)
            print(f"Downloaded file from {remote_path} to {local_path}")
        except Exception as e:
            raise IOError(f"Failed to download {remote_path}: {e}")
    def upload_file(self, file_path, destination_path):
        try:
            self.sftp.put(file_path, destination_path)
            print(f"Uploaded {file_path} to {destination_path}")
        except Exception as e:
            raise IOError(f"Failed to upload {file_path}: {e}")
    def close(self):
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print("SFTP connection closed.")

class FTPClient:
    def __init__(self, config):
        self.host = config['NCBI_ftp_host']
        self.username = config['NCBI_username']
        self.password = config['NCBI_password']
        self.port = config.get('port', 21)  # Default FTP port is 21
        self.ftp = None
    def connect(self):
        try:
            # Connect to FTP host and login
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(user=self.username, passwd=self.password)
            print(f"Connected to FTP: {self.host}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to FTP: {e}")
    def change_dir(self, dir_path):
        try:
            self.ftp.cwd(dir_path)  # Try to change to the directory
        except ftplib.error_perm:
            self.ftp.mkd(dir_path)  # Create the directory if it doesn't exist
            self.ftp.cwd(dir_path)  # Change to the newly created directory
        print(f"Changed directories to {dir_path}")
    def file_exists(self, file_path):
        if file_path in self.ftp.nlst():
            return True
        else:
            return False
    def download_file(self, remote_path, local_path):
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary(f'RETR {remote_path}', f.write)
        print(f"Downloaded file from {remote_path} to {local_path}")
    def upload_file(self, file_path, destination_path):
        try:
            if file_path.endswith(('.fasta', '.fastq', '.gff', '.gz', 'xml')):  
                with open(file_path, 'rb') as file:
                    print(f"Uploading binary file: {file_path}")
                    self.ftp.storbinary(f'STOR {destination_path}', file)
            else:
                with open(file_path, 'r') as file:
                    print(f"Uploading text file: {file_path}")
                    self.ftp.storlines(f'STOR {destination_path}', file)
                # Open the file and upload it
            print(f"Uploaded {file_path} to {destination_path}")
        except Exception as e:
            raise IOError(f"Failed to upload {file_path}: {e}")
    def close(self):
        if self.ftp:
            try:
                self.ftp.quit()  # Gracefully close the connection
            except Exception:
                self.ftp.close()  # Force close if quit() fails
        print("FTP connection closed.")

class XMLSubmission(ABC):
    def __init__(self, sample, submission_config, metadata_df, output_dir):
        self.sample = sample
        self.submission_config = submission_config
        self.output_dir = output_dir
        parser = MetadataParser(metadata_df)
        self.top_metadata = parser.extract_top_metadata()
    def safe_text(self, value):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return "Not Provided"
        return str(value)
    def create_xml(self, output_dir):
        # Root element
        submission = ET.Element('Submission')
        # Description block (common across all submissions)
        description = ET.SubElement(submission, 'Description')
        title = ET.SubElement(description, 'Title')
        title.text = self.safe_text(self.top_metadata['title'])
        comment = ET.SubElement(description, 'Comment')
        comment.text = self.safe_text(self.top_metadata['description'])
        # Organization block (common across all submissions)
        organization_el = ET.SubElement(description, 'Organization', {
            'type': self.submission_config['Type'],
            'role': self.submission_config['Role'],
            'org_id': self.submission_config['Org_ID']
        })
        name = ET.SubElement(organization_el, 'Name')
        name.text = self.safe_text(self.submission_config['Submitting_Org'])
        # Contact block (common across all submissions)
        contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.submission_config['Email']})
        contact_name = ET.SubElement(contact_el, 'Name')
        first = ET.SubElement(contact_name, 'First')
        first.text = self.safe_text(self.submission_config['Submitter']['Name']['First'])
        last = ET.SubElement(contact_name, 'Last')
        last.text = self.safe_text(self.submission_config['Submitter']['Name']['Last'])
        # Call subclass-specific methods to add the unique parts
        self.add_action_block(submission)
        self.add_attributes_block(submission)
        # Save the XML to file
        xml_output_path = os.path.join(output_dir, "submission.xml")
        os.makedirs(os.path.dirname(xml_output_path), exist_ok=True)
        rough_string = ET.tostring(submission, encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        with open(xml_output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        print(f"XML generated at {xml_output_path}")
        return xml_output_path
    @abstractmethod
    def add_action_block(self, submission):
        """Add the action block, which differs between submissions."""
        pass
    @abstractmethod
    def add_attributes_block(self, submission):
        """Add the attributes block, which differs between submissions."""
        pass

# todo: don't think I need separate classes for each db
class BiosampleSubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type) 
        # Use the MetadataParser to extract metadata
        parser = MetadataParser(metadata_df)
        self.top_metadata = parser.extract_top_metadata()
        self.biosample_metadata = parser.extract_biosample_metadata()
        # Generate the BioSample XML upon initialization
        self.xml_output_path = self.create_xml(output_dir) 
    def add_action_block(self, submission):
        action = ET.SubElement(submission, 'Action')
        add_data = ET.SubElement(action, 'AddData', {'target_db': 'BioSample'})
        data = ET.SubElement(add_data, 'Data', {'content_type': 'xml'})
        xml_content = ET.SubElement(data, 'XmlContent')
        # BioSample-specific XML elements
        biosample = ET.SubElement(xml_content, 'BioSample', {'schema_version': '2.0'})
        sample_id = ET.SubElement(biosample, 'SampleId')
        spuid = ET.SubElement(sample_id, 'SPUID', {'spuid_namespace': ''})
        spuid.text = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
    def add_attributes_block(self, submission):
        biosample = submission.find(".//BioSample")
        attributes = ET.SubElement(biosample, 'Attributes')
        for attr_name, attr_value in self.biosample_metadata.items():
            attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
            attribute.text = self.safe_text(attr_value)
    def submit(self):
        # Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
        submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
        with open(submit_ready_file, 'w') as fp:
            pass 
        # Submit files
        files_to_submit = [submit_ready_file, self.xml_output_path]
        self.submit_files(files_to_submit, 'biosample')
        print(f"Submitted sample {self.sample.sample_id} to BioSample")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()

class SRASubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type) 
        # Use the MetadataParser to extract metadata
        parser = MetadataParser(metadata_df)
        self.top_metadata = parser.extract_top_metadata()
        self.sra_metadata = parser.extract_sra_metadata()
        # Generate the BioSample XML upon initialization
        self.xml_output_path = self.create_xml(output_dir) 
    def add_action_block(self, submission):
        action = ET.SubElement(submission, "Action")
        add_files = ET.SubElement(action, "AddFiles", target_db="SRA")
        file1 = ET.SubElement(add_files, "File", file_path=self.sample.fastq1)
        data_type1 = ET.SubElement(file1, "DataType")
        data_type1.text = "generic-data"
        file2 = ET.SubElement(add_files, "File", file_path=self.sample.fastq2)
        data_type2 = ET.SubElement(file2, "DataType")
        data_type2.text = "generic-data"
    def add_attributes_block(self, submission):
        add_files = submission.find(".//AddFiles")
        attributes = ET.SubElement(add_files, 'Attributes')
        for attr_name, attr_value in self.sra_metadata.items():
            attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
            attribute.text = self.safe_text(attr_value)
    def submit(self):
        # Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
        submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
        with open(submit_ready_file, 'w') as fp:
            pass 
        # Submit files
        files_to_submit = [submit_ready_file, self.xml_output_path, self.sample.fastq1, self.sample.fastq2]
        self.submit_files(files_to_submit, 'sra')
        print(f"Submitted sample {self.sample.sample_id} to SRA")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()

class GenbankSubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type)
        # Use the MetadataParser to extract metadata
        parser = MetadataParser(metadata_df)
        self.top_metadata = parser.extract_top_metadata()
        self.genbank_metadata = parser.extract_genbank_metadata()
        # Generate the BioSample XML upon initialization
        self.xml_output_path = self.create_xml(output_dir) 
    def add_action_block(self, submission):
        action = ET.SubElement(submission, "Action")
        add_files = ET.SubElement(action, "AddFiles", target_db="Genbank")
        file1 = ET.SubElement(add_files, "File", file_path=self.sample.fasta_file)
        data_type1 = ET.SubElement(file1, "DataType")
        data_type1.text = "generic-data" 
        file2 = ET.SubElement(add_files, "File", file_path=self.sample.annotation_file)
        data_type2 = ET.SubElement(file2, "DataType")
        data_type2.text = "generic-data"
    def add_attributes_block(self, submission):
        add_files = submission.find(".//AddFiles")   
        # Meta and Genome information
        meta_el = ET.SubElement(add_files, "Meta", content_type="XML")
        xml_content = ET.SubElement(meta_el, "XmlContent")
        genome = ET.SubElement(xml_content, "Genome")
        description = ET.SubElement(genome, "Description")
        assembly_metadata_choice = ET.SubElement(description, "GenomeAssemblyMetadataChoice")
        assembly_metadata = ET.SubElement(assembly_metadata_choice, "GenomeAssemblyMetadata")
        sequencing_technologies = ET.SubElement(assembly_metadata, "SequencingTechnologies", self.genbank_metadata['mean_coverage'])
        technology = ET.SubElement(sequencing_technologies, "Technology")
        technology.text = self.genbank_metadata['assembly_protocol']
        assembly = ET.SubElement(assembly_metadata, "Assembly")
        method = ET.SubElement(assembly, "Method")
        method.text = self.genbank_metadata['assembly_method']
        genome_representation = ET.SubElement(description, "GenomeRepresentation")
        genome_representation.text = "Full"
        # Authors
        sequence_authors = ET.SubElement(description, "SequenceAuthors")
        authors_list = self.genbank_metadata['authors'].split('; ')
        for i, author in enumerate(authors_list, start=1):
            author_el = ET.SubElement(sequence_authors, "Author")
            name_el = ET.SubElement(author_el, "Name")
            # Split the author's name into components
            name_parts = author.split()
            # Parse first, middle (if exists), and last name
            first_name = name_parts[0]
            last_name = name_parts[-1]
            middle_name = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else None
            # Add First element
            first_el = ET.SubElement(name_el, "First")
            first_el.text = first_name
            # Add Last element
            last_el = ET.SubElement(name_el, "Last")
            last_el.text = last_name
            # Add Middle element if there is one
            if middle_name:
                middle_el = ET.SubElement(name_el, "Middle")
                middle_el.text = middle_name
        # Publication
        #todo: db_type?
        publication = ET.SubElement(description, "Publication", status=self.genbank_metadata['publication_status'], id=self.genbank_metadata['publication_title'])
        db_type = ET.SubElement(publication, "DbType")
        db_type.text = "ePubmed"
        # Additional attributes
        ET.SubElement(description, "ExpectedFinalVersion").text = "Yes"
        ET.SubElement(description, "AnnotateWithPGAP").text = "No"
        # BioProject and BioSample references
        attribute_ref1 = ET.SubElement(add_files, "AttributeRefId")
        ref_id1 = ET.SubElement(attribute_ref1, "RefId")
        primary_id1 = ET.SubElement(ref_id1, "PrimaryId", db="BioProject")
        primary_id1.text = self.top_metadata['ncbi-bioproject']
        attribute_ref2 = ET.SubElement(add_files, "AttributeRefId")
        ref_id2 = ET.SubElement(attribute_ref2, "RefId")
        primary_id2 = ET.SubElement(ref_id2, "PrimaryId", db="BioSample")
        # todo: need to figure out BioSample 
        primary_id2.text = ""
        # Identifier
        identifier = ET.SubElement(add_files, "Identifier")
        spuid = ET.SubElement(identifier, "SPUID", spuid_namespace="NCBI")
        spuid.text = self.top_metadata['ncbi-spuid_namespace']        
    def submit(self):
        # Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
        submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
        with open(submit_ready_file, 'w') as fp:
            pass 
        # Submit files
        files_to_submit = [submit_ready_file, self.xml_output_path, self.sample.fasta_file, self.sample.annotation_file]
        self.submit_files(files_to_submit, 'genbank')
        print(f"Submitted sample {self.sample.sample_id} to Genbank")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()

        # Finish file prep

    # get locus tag from gff file for Table2asn submission
    # todo: the locus tag needs to be fetched (?) after BioSample is assigned (it appears under Manage Data for the BioProject)
    def get_gff_locus_tag(self):
        """ Read the locus lag from the GFF3 file for use in table2asn command"""
        locus_tag = None
        with open(self.sample.annotation_file, 'r') as file:
            for line in file:
                if line.startswith('##FASTA'):
                    break  # Stop reading if FASTA section starts
                elif line.startswith('#'):
                    continue  # Skip comment lines
                else:
                    columns = line.strip().split('\t')
                    if columns[2] == 'CDS':
                        attributes = columns[8].split(';')
                        for attribute in attributes:
                            key, value = attribute.split('=')
                            if key == 'locus_tag':
                                locus_tag = value.split('_')[0]
                                break  # Found locus tag, stop searching
                        if locus_tag:
                            break  # Found locus tag, stop searching
        return locus_tag
    
    #  Detect multiple contig fasta for Table2asn submission
    def is_multicontig_fasta(self):
        headers = set()
        with open(self.sample.fasta, 'r') as file:
            for line in file:
                if line.startswith('>'):
                    headers.add(line.strip())
                    if len(headers) > 1:
                        return True
        return False
    
    def run_table2asn(self):
        """
        Executes table2asn with appropriate flags and handles errors.
        """
        print("Running table2asn...")
        # Check if table2asn executable exists in PATH
        table2asn_path = shutil.which('table2asn')
        if not table2asn_path:
            raise FileNotFoundError("table2asn executable not found in PATH.")
        # Check if a GFF file is supplied and extract the locus tag
        # todo: this needs to be changed - see Mike's comment in NCBI UI-less doc
        locus_tag = self.extract_locus_tag(self.sample.annotation_file)
        # Construct the table2asn command
        cmd = [
            "table2asn",
            "-i", "sequence.fsa",
            "-f", "source.src",
            "-o", f"{self.sample.id}.sqn",
            "-t", "authorset.sbt",
            "-f", self.sample.annotation_file 
        ]
        if locus_tag:
            cmd.extend(["-l", locus_tag])
        if self.is_multicontig_fasta(self.sample.fasta):
            cmd.append("-M")
            cmd.append("n")
            cmd.append("-Z")
        if os.path.isfile("comment.cmt"):
            cmd.append("-w")
            cmd.append("comment.cmt")
        # Run the command and capture errors
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"table2asn output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            print(f"Error running table2asn: {e.stderr}")
            raise
    def create_zip_files(self):
        # Code for creating a zip archive for Genbank submission
        print("Creating zip files...")



if __name__ == "__main__":
    submission_main()