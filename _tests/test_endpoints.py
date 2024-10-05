# -*- coding: utf-8 -*-
import requests
import pytest
from collections import namedtuple
import glob
import os
import json
import logging

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

EndpointTest = namedtuple('EndpointTest', ['chain', 'endpoint', 'provider', 'address'])

# Set this to False to ignore the whitelist and process all providers
use_whitelist = True

# Whitelist for specific providers per chain
whitelist = {
    'osmosis': ['Osmosis Foundation', 'Polkachu', "Lavender.Five Nodes 🐝"]
    
} if use_whitelist else {}

def log_request_details(test_case, response):
    logging.info(f"Testing {test_case.chain}-{test_case.endpoint.upper()}-{test_case.provider}")
    logging.info(f"Request URL: {response.url}")
    logging.info(f"Response Status Code: {response.status_code}")
    logging.info(f"Response Body: {response.text}")

def generate_endpoint_tests():
    test_cases = []
    logging.info(f"Current working directory: {os.getcwd()}")
    files_found = glob.glob('**/chain.json', recursive=True)
    for filename in files_found:
        with open(filename) as f:
            data = json.load(f)
            chain_name = data.get('chain_name', 'unknown')
            if 'apis' in data:
                for api_type in ['rpc', 'rest']:
                    for api in data['apis'].get(api_type, []):
                        if 'provider' in api and (not use_whitelist or api['provider'] in whitelist.get(chain_name, [])):
                            address = api['address']
                            if api_type == 'rpc':
                                address += '/status'
                            elif api_type == 'rest':
                                address += '/cosmos/base/tendermint/v1beta1/syncing'
                            test_cases.append(EndpointTest(chain=chain_name, endpoint=api_type, provider=api['provider'], address=address))
    return test_cases

test_cases = generate_endpoint_tests()
if test_cases:
    @pytest.mark.parametrize("test_case", test_cases, ids=lambda test_case: f"{test_case.chain.upper()}-{test_case.endpoint.upper()}-{test_case.provider}")
    def test_endpoint_availability(test_case):
        response = requests.get(test_case.address)
        log_request_details(test_case, response)
        assert response.status_code == 200, f"{test_case.chain.upper()}-{test_case.endpoint.upper()}-{test_case.provider} endpoint not reachable"
else:
    logging.error("Skipping tests due to no valid test cases.")