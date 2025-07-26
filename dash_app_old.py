import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import glob
import os
from collections import defaultdict
import pickle
from postcode_dataset import UKPostcodeDataset

class UKHousePriceDashboard:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.df = None
        
        # Initialize the UK postcode dataset for accurate geocoding
        print("Initializing UK postcode dataset...")
        self.postcode_geocoder = UKPostcodeDataset()
        
        # Load postcode data (this will use cached data if available)
        if not self.postcode_geocoder.load_postcode_data():
            print("Warning: Failed to load postcode dataset. Coordinates may be inaccurate.")
            self.postcode_geocoder = None

    def get_coordinates(self, postcode):
        """Get accurate coordinates for a postcode using the real dataset"""
        if self.postcode_geocoder:
            return self.postcode_geocoder.get_coordinates(postcode)
        else:
            # Fallback to Central London if dataset not available
            return 51.5074, -0.1278
            'N2': {'lat': 51.5889, 'lon': -0.1651, 'name': 'East Finchley/Barnet'},  # This is where N2 9QL should be
            'N3': {'lat': 51.5976, 'lon': -0.1787, 'name': 'Finchley Central'},
            'N4': {'lat': 51.5706, 'lon': -0.1057, 'name': 'Finsbury Park'},
            'N5': {'lat': 51.5584, 'lon': -0.1028, 'name': 'Highbury'},
            'N6': {'lat': 51.5846, 'lon': -0.1460, 'name': 'Highgate'},
            'N7': {'lat': 51.5523, 'lon': -0.1173, 'name': 'Holloway'},
            'N8': {'lat': 51.5884, 'lon': -0.1247, 'name': 'Hornsey'},
            'N9': {'lat': 51.6197, 'lon': -0.0433, 'name': 'Lower Edmonton'},
            'N10': {'lat': 51.5934, 'lon': -0.1436, 'name': 'Muswell Hill'},
            'N11': {'lat': 51.6115, 'lon': -0.1366, 'name': 'New Southgate'},
            'N12': {'lat': 51.6166, 'lon': -0.1779, 'name': 'North Finchley'},
            'N13': {'lat': 51.6157, 'lon': -0.1020, 'name': 'Palmers Green'},
            'N14': {'lat': 51.6321, 'lon': -0.1105, 'name': 'Southgate'},
            'N15': {'lat': 51.5934, 'lon': -0.0751, 'name': 'Seven Sisters'},
            'N16': {'lat': 51.5634, 'lon': -0.0750, 'name': 'Stoke Newington'},
            'N17': {'lat': 51.5934, 'lon': -0.0567, 'name': 'Tottenham'},
            'N18': {'lat': 51.6055, 'lon': -0.0433, 'name': 'Upper Edmonton'},
            'N19': {'lat': 51.5656, 'lon': -0.1340, 'name': 'Upper Holloway'},
            'N20': {'lat': 51.6166, 'lon': -0.1779, 'name': 'Whetstone'},
            'N21': {'lat': 51.6520, 'lon': -0.1105, 'name': 'Winchmore Hill'},
            'N22': {'lat': 51.5934, 'lon': -0.1247, 'name': 'Wood Green'},
            
            # North West London postcodes
            'NW1': {'lat': 51.5454, 'lon': -0.1576, 'name': 'Camden/Regent\'s Park'},
            'NW2': {'lat': 51.5591, 'lon': -0.2135, 'name': 'Cricklewood'},
            'NW3': {'lat': 51.5591, 'lon': -0.1787, 'name': 'Hampstead'},
            'NW4': {'lat': 51.6166, 'lon': -0.2135, 'name': 'Hendon'},
            'NW5': {'lat': 51.5591, 'lon': -0.1460, 'name': 'Kentish Town'},
            'NW6': {'lat': 51.5434, 'lon': -0.1936, 'name': 'West Hampstead'},
            'NW7': {'lat': 51.6320, 'lon': -0.2487, 'name': 'Mill Hill'},
            'NW8': {'lat': 51.5329, 'lon': -0.1717, 'name': 'St John\'s Wood'},
            'NW9': {'lat': 51.6055, 'lon': -0.2708, 'name': 'Colindale'},
            'NW10': {'lat': 51.5329, 'lon': -0.2487, 'name': 'Willesden'},
            'NW11': {'lat': 51.5770, 'lon': -0.2135, 'name': 'Golders Green'},
            
            # East London postcodes
            'E1': {'lat': 51.5154, 'lon': -0.0648, 'name': 'Whitechapel'},
            'E2': {'lat': 51.5329, 'lon': -0.0648, 'name': 'Bethnal Green'},
            'E3': {'lat': 51.5329, 'lon': -0.0254, 'name': 'Bow'},
            'E4': {'lat': 51.6055, 'lon': 0.0096, 'name': 'Chingford'},
            'E5': {'lat': 51.5591, 'lon': -0.0567, 'name': 'Clapton'},
            'E6': {'lat': 51.5329, 'lon': 0.0576, 'name': 'East Ham'},
            'E7': {'lat': 51.5454, 'lon': 0.0315, 'name': 'Forest Gate'},
            'E8': {'lat': 51.5454, 'lon': -0.0567, 'name': 'Hackney'},
            'E9': {'lat': 51.5454, 'lon': -0.0346, 'name': 'Homerton'},
            'E10': {'lat': 51.5591, 'lon': -0.0254, 'name': 'Leyton'},
            'E11': {'lat': 51.5591, 'lon': 0.0096, 'name': 'Leytonstone'},
            'E12': {'lat': 51.5454, 'lon': 0.0315, 'name': 'Manor Park'},
            'E13': {'lat': 51.5329, 'lon': 0.0315, 'name': 'Plaistow'},
            'E14': {'lat': 51.5054, 'lon': -0.0196, 'name': 'Poplar/Canary Wharf'},
            'E15': {'lat': 51.5434, 'lon': -0.0033, 'name': 'Stratford'},
            'E16': {'lat': 51.5154, 'lon': 0.0315, 'name': 'Canning Town'},
            'E17': {'lat': 51.5884, 'lon': -0.0254, 'name': 'Walthamstow'},
            'E18': {'lat': 51.5934, 'lon': 0.0315, 'name': 'South Woodford'},
            
            # South East London postcodes
            'SE1': {'lat': 51.5054, 'lon': -0.0922, 'name': 'Southwark'},
            'SE2': {'lat': 51.4904, 'lon': 0.1826, 'name': 'Abbey Wood'},
            'SE3': {'lat': 51.4634, 'lon': 0.0315, 'name': 'Blackheath'},
            'SE4': {'lat': 51.4634, 'lon': -0.0346, 'name': 'Brockley'},
            'SE5': {'lat': 51.4724, 'lon': -0.0922, 'name': 'Camberwell'},
            'SE6': {'lat': 51.4454, 'lon': -0.0196, 'name': 'Catford'},
            'SE7': {'lat': 51.4814, 'lon': 0.0935, 'name': 'Charlton'},
            'SE8': {'lat': 51.4904, 'lon': -0.0346, 'name': 'Deptford'},
            'SE9': {'lat': 51.4364, 'lon': 0.0696, 'name': 'Eltham'},
            'SE10': {'lat': 51.4814, 'lon': -0.0033, 'name': 'Greenwich'},
            'SE11': {'lat': 51.4904, 'lon': -0.1173, 'name': 'Kennington'},
            'SE12': {'lat': 51.4454, 'lon': 0.0096, 'name': 'Lee'},
            'SE13': {'lat': 51.4634, 'lon': -0.0033, 'name': 'Lewisham'},
            'SE14': {'lat': 51.4724, 'lon': -0.0346, 'name': 'New Cross'},
            'SE15': {'lat': 51.4724, 'lon': -0.0648, 'name': 'Peckham'},
            'SE16': {'lat': 51.4954, 'lon': -0.0509, 'name': 'Rotherhithe'},
            'SE17': {'lat': 51.4904, 'lon': -0.1046, 'name': 'Walworth'},
            'SE18': {'lat': 51.4904, 'lon': 0.0935, 'name': 'Woolwich'},
            
            # South West London postcodes  
            'SW1': {'lat': 51.4954, 'lon': -0.1423, 'name': 'Westminster'},
            'SW2': {'lat': 51.4454, 'lon': -0.1173, 'name': 'Brixton'},
            'SW3': {'lat': 51.4904, 'lon': -0.1673, 'name': 'Chelsea'},
            'SW4': {'lat': 51.4634, 'lon': -0.1423, 'name': 'Clapham'},
            'SW5': {'lat': 51.4814, 'lon': -0.1936, 'name': 'Earl\'s Court'},
            'SW6': {'lat': 51.4724, 'lon': -0.2017, 'name': 'Fulham'},
            'SW7': {'lat': 51.4954, 'lon': -0.1717, 'name': 'South Kensington'},
            'SW8': {'lat': 51.4724, 'lon': -0.1301, 'name': 'South Lambeth'},
            'SW9': {'lat': 51.4634, 'lon': -0.1173, 'name': 'Stockwell'},
            'SW10': {'lat': 51.4854, 'lon': -0.1936, 'name': 'West Brompton'},
            'SW11': {'lat': 51.4634, 'lon': -0.1673, 'name': 'Battersea'},
            'SW12': {'lat': 51.4364, 'lon': -0.1173, 'name': 'Balham'},
            'SW13': {'lat': 51.4634, 'lon': -0.2405, 'name': 'Barnes'},
            'SW14': {'lat': 51.4454, 'lon': -0.2613, 'name': 'Mortlake'},
            'SW15': {'lat': 51.4364, 'lon': -0.2187, 'name': 'Putney'},
            'SW16': {'lat': 51.4184, 'lon': -0.1173, 'name': 'Streatham'},
            'SW17': {'lat': 51.4274, 'lon': -0.1673, 'name': 'Tooting'},
            'SW18': {'lat': 51.4454, 'lon': -0.1936, 'name': 'Wandsworth'},
            'SW19': {'lat': 51.4184, 'lon': -0.1936, 'name': 'Wimbledon'},
            'SW20': {'lat': 51.4094, 'lon': -0.1936, 'name': 'Raynes Park'},
            
            # West London postcodes
            'W1': {'lat': 51.5154, 'lon': -0.1423, 'name': 'Marylebone/Mayfair'},
            'W2': {'lat': 51.5154, 'lon': -0.1717, 'name': 'Paddington'},
            'W3': {'lat': 51.5154, 'lon': -0.2487, 'name': 'Acton'},
            'W4': {'lat': 51.4904, 'lon': -0.2613, 'name': 'Chiswick'},
            'W5': {'lat': 51.5154, 'lon': -0.3080, 'name': 'Ealing'},
            'W6': {'lat': 51.4904, 'lon': -0.2268, 'name': 'Hammersmith'},
            'W7': {'lat': 51.5154, 'lon': -0.3392, 'name': 'Hanwell'},
            'W8': {'lat': 51.5054, 'lon': -0.1936, 'name': 'Kensington'},
            'W9': {'lat': 51.5254, 'lon': -0.1717, 'name': 'Maida Vale'},
            'W10': {'lat': 51.5254, 'lon': -0.2268, 'name': 'Ladbroke Grove'},
            'W11': {'lat': 51.5154, 'lon': -0.2017, 'name': 'Notting Hill'},
            'W12': {'lat': 51.5054, 'lon': -0.2268, 'name': 'Shepherd\'s Bush'},
            'W13': {'lat': 51.5054, 'lon': -0.3392, 'name': 'West Ealing'},
            'W14': {'lat': 51.4954, 'lon': -0.2017, 'name': 'West Kensington'},
            
            # Central London postcodes
            'EC1': {'lat': 51.5254, 'lon': -0.1046, 'name': 'Clerkenwell'},
            'EC2': {'lat': 51.5154, 'lon': -0.0922, 'name': 'Bank/Moorgate'},
            'EC3': {'lat': 51.5104, 'lon': -0.0796, 'name': 'Monument/Tower'},
            'EC4': {'lat': 51.5154, 'lon': -0.1046, 'name': 'Fleet Street/St Paul\'s'},
            'WC1': {'lat': 51.5254, 'lon': -0.1270, 'name': 'Bloomsbury'},
            'WC2': {'lat': 51.5154, 'lon': -0.1270, 'name': 'Covent Garden'},
            
            # Outer London areas with specific postcodes
            'BR1': {'lat': 51.4054, 'lon': 0.0196, 'name': 'Bromley'},
            'BR2': {'lat': 51.3844, 'lon': 0.0315, 'name': 'Hayes (Bromley)'},
            'CR0': {'lat': 51.3744, 'lon': -0.0922, 'name': 'Croydon'},
            'CR4': {'lat': 51.3844, 'lon': -0.1423, 'name': 'Mitcham'},
            'CR7': {'lat': 51.3544, 'lon': -0.0648, 'name': 'Thornton Heath'},
            'DA1': {'lat': 51.4444, 'lon': 0.2196, 'name': 'Dartford'},
            'DA5': {'lat': 51.4244, 'lon': 0.1826, 'name': 'Bexley'},
            'DA6': {'lat': 51.4364, 'lon': 0.1196, 'name': 'Bexleyheath'},
            'DA7': {'lat': 51.4444, 'lon': 0.1436, 'name': 'Bexleyheath'},
            'DA8': {'lat': 51.4844, 'lon': 0.1826, 'name': 'Erith'},
            'EN1': {'lat': 51.6520, 'lon': -0.0796, 'name': 'Enfield'},
            'EN2': {'lat': 51.6366, 'lon': -0.0796, 'name': 'Enfield'},
            'HA0': {'lat': 51.5591, 'lon': -0.3173, 'name': 'Wembley'},
            'HA1': {'lat': 51.5591, 'lon': -0.3467, 'name': 'Harrow'},
            'HA2': {'lat': 51.5770, 'lon': -0.3467, 'name': 'Harrow'},
            'HA3': {'lat': 51.5770, 'lon': -0.3762, 'name': 'Harrow Weald'},
            'HA4': {'lat': 51.5434, 'lon': -0.4480, 'name': 'Ruislip'},
            'HA5': {'lat': 51.5769, 'lon': -0.4187, 'name': 'Pinner'},
            'HA6': {'lat': 51.5591, 'lon': -0.4480, 'name': 'Northwood'},
            'HA7': {'lat': 51.6055, 'lon': -0.4187, 'name': 'Stanmore'},
            'HA8': {'lat': 51.6166, 'lon': -0.2889, 'name': 'Edgware'},
            'HA9': {'lat': 51.5591, 'lon': -0.2889, 'name': 'Wembley'},
            'IG1': {'lat': 51.5885, 'lon': 0.0819, 'name': 'Ilford'},
            'IG2': {'lat': 51.5885, 'lon': 0.1196, 'name': 'Gants Hill'},
            'IG3': {'lat': 51.5885, 'lon': 0.1436, 'name': 'Seven Kings'},
            'IG4': {'lat': 51.5885, 'lon': 0.1826, 'name': 'Redbridge'},
            'IG5': {'lat': 51.5885, 'lon': 0.1436, 'name': 'Clayhall'},
            'IG6': {'lat': 51.6055, 'lon': 0.0819, 'name': 'Barkingside'},
            'IG7': {'lat': 51.6166, 'lon': 0.0819, 'name': 'Chigwell'},
            'IG8': {'lat': 51.6055, 'lon': 0.0435, 'name': 'Woodford Green'},
            'IG9': {'lat': 51.6055, 'lon': 0.0196, 'name': 'Buckhurst Hill'},
            'IG10': {'lat': 51.6320, 'lon': 0.0196, 'name': 'Loughton'},
            'IG11': {'lat': 51.5591, 'lon': 0.0819, 'name': 'Barking'},
            'KT1': {'lat': 51.4094, 'lon': -0.3010, 'name': 'Kingston upon Thames'},
            'KT2': {'lat': 51.4184, 'lon': -0.2790, 'name': 'Kingston upon Thames'},
            'KT3': {'lat': 51.4034, 'lon': -0.2790, 'name': 'New Malden'},
            'KT4': {'lat': 51.3784, 'lon': -0.2565, 'name': 'Worcester Park'},
            'KT5': {'lat': 51.3934, 'lon': -0.2405, 'name': 'Surbiton'},
            'KT6': {'lat': 51.3934, 'lon': -0.2790, 'name': 'Surbiton'},
            'RM1': {'lat': 51.5779, 'lon': 0.2120, 'name': 'Romford'},
            'RM2': {'lat': 51.5779, 'lon': 0.2500, 'name': 'Gidea Park'},
            'RM3': {'lat': 51.5779, 'lon': 0.2880, 'name': 'Harold Wood'},
            'RM4': {'lat': 51.5779, 'lon': 0.3260, 'name': 'Noak Hill'},
            'RM5': {'lat': 51.5779, 'lon': 0.1826, 'name': 'Collier Row'},
            'RM6': {'lat': 51.5591, 'lon': 0.1826, 'name': 'Chadwell Heath'},
            'RM7': {'lat': 51.5434, 'lon': 0.1826, 'name': 'Rush Green'},
            'RM8': {'lat': 51.5329, 'lon': 0.1466, 'name': 'Becontree'},
            'RM9': {'lat': 51.5434, 'lon': 0.1196, 'name': 'Becontree Heath'},
            'RM10': {'lat': 51.5434, 'lon': 0.0935, 'name': 'Dagenham'},
            'RM11': {'lat': 51.5779, 'lon': 0.1436, 'name': 'Emerson Park'},
            'RM12': {'lat': 51.5591, 'lon': 0.2196, 'name': 'Hornchurch'},
            'RM13': {'lat': 51.5329, 'lon': 0.2196, 'name': 'Rainham'},
            'RM14': {'lat': 51.5154, 'lon': 0.2196, 'name': 'Upminster'},
            'SM1': {'lat': 51.3616, 'lon': -0.1933, 'name': 'Sutton'},
            'SM2': {'lat': 51.3616, 'lon': -0.2187, 'name': 'Belmont'},
            'SM3': {'lat': 51.3844, 'lon': -0.2187, 'name': 'Cheam'},
            'SM4': {'lat': 51.3934, 'lon': -0.1673, 'name': 'Morden'},
            'SM5': {'lat': 51.3484, 'lon': -0.1933, 'name': 'Carshalton'},
            'SM6': {'lat': 51.3484, 'lon': -0.1673, 'name': 'Wallington'},
            'TW1': {'lat': 51.4634, 'lon': -0.3310, 'name': 'Twickenham'},
            'TW2': {'lat': 51.4634, 'lon': -0.3467, 'name': 'Whitton'},
            'TW3': {'lat': 51.4724, 'lon': -0.3762, 'name': 'Hounslow'},
            'TW4': {'lat': 51.4634, 'lon': -0.3762, 'name': 'Hounslow West'},
            'TW5': {'lat': 51.4814, 'lon': -0.3762, 'name': 'Heston'},
            'TW6': {'lat': 51.4634, 'lon': -0.4187, 'name': 'Heathrow'},
            'TW7': {'lat': 51.4904, 'lon': -0.3467, 'name': 'Isleworth'},
            'TW8': {'lat': 51.4904, 'lon': -0.3173, 'name': 'Brentford'},
            'TW9': {'lat': 51.4634, 'lon': -0.2890, 'name': 'Richmond'},
            'TW10': {'lat': 51.4634, 'lon': -0.3010, 'name': 'Ham'},
            'TW11': {'lat': 51.4274, 'lon': -0.3310, 'name': 'Teddington'},
            'TW12': {'lat': 51.4184, 'lon': -0.3467, 'name': 'Hampton'},
            'TW13': {'lat': 51.4094, 'lon': -0.3762, 'name': 'Feltham'},
            'TW14': {'lat': 51.4184, 'lon': -0.4187, 'name': 'Hatton'},
            'TW15': {'lat': 51.3894, 'lon': -0.4480, 'name': 'Ashford'},
            'TW16': {'lat': 51.3734, 'lon': -0.4187, 'name': 'Sunbury'},
            'TW17': {'lat': 51.3734, 'lon': -0.3762, 'name': 'Shepperton'},
            'TW18': {'lat': 51.3894, 'lon': -0.3467, 'name': 'Staines'},
            'TW19': {'lat': 51.4184, 'lon': -0.5104, 'name': 'Stanwell'},
            'TW20': {'lat': 51.3934, 'lon': -0.5104, 'name': 'Egham'},
            'UB1': {'lat': 51.5154, 'lon': -0.4813, 'name': 'Southall'},
            'UB2': {'lat': 51.5154, 'lon': -0.4480, 'name': 'Southall'},
            'UB3': {'lat': 51.5329, 'lon': -0.4813, 'name': 'Hayes'},
            'UB4': {'lat': 51.5329, 'lon': -0.4480, 'name': 'Hayes'},
            'UB5': {'lat': 51.5434, 'lon': -0.4813, 'name': 'Northolt'},
            'UB6': {'lat': 51.5434, 'lon': -0.4480, 'name': 'Greenford'},
            'UB7': {'lat': 51.5329, 'lon': -0.5104, 'name': 'West Drayton'},
            'UB8': {'lat': 51.5434, 'lon': -0.4813, 'name': 'Uxbridge'},
            'UB9': {'lat': 51.5591, 'lon': -0.4813, 'name': 'Uxbridge'},
            'UB10': {'lat': 51.5434, 'lon': -0.4480, 'name': 'Hillingdon'},
        }
    
    def load_coords_cache(self):
        if os.path.exists(self.coords_cache_file):
            with open(self.coords_cache_file, 'rb') as f:
                self.postcode_coords = pickle.load(f)
    
    def estimate_coordinates(self, postcode):
        """Estimate coordinates based on postcode prefix with high accuracy for London"""
        if not postcode:
            return None, None
            
        # Extract postcode area (handle both single and double letter prefixes)
        postcode_parts = postcode.split()
        if not postcode_parts:
            return None, None
            
        postcode_prefix = postcode_parts[0]
        
        # Try different postcode area patterns in order of specificity
        postcode_areas_to_try = []
        
        if len(postcode_prefix) >= 2:
            # Try full district first (e.g., "N2", "NW7", "SW1A" -> "SW1")
            # Extract letters and first digit
            letters = ''.join([c for c in postcode_prefix if c.isalpha()])
            digits = ''.join([c for c in postcode_prefix if c.isdigit()])
            
            if letters and digits:
                # Try letter + first digit (e.g., "N2", "NW7")
                district = letters + digits[0]
                postcode_areas_to_try.append(district)
            
            # Try just letters (e.g., "NW", "SW")
            if letters:
                postcode_areas_to_try.append(letters)
        
        # Try first character as last resort
        if postcode_prefix:
            postcode_areas_to_try.append(postcode_prefix[0])
        
        # Find matching region
        for area in postcode_areas_to_try:
            if area in self.uk_postcode_regions:
                region = self.uk_postcode_regions[area]
                # Add minimal random variation to avoid exact overlaps
                lat_noise = self.rng.normal(0, 0.005)  # Very small noise for accuracy
                lon_noise = self.rng.normal(0, 0.005)
                return region['lat'] + lat_noise, region['lon'] + lon_noise
        
        # Default to Central London with variation if no match found
        lat_noise = self.rng.normal(0, 0.01)
        lon_noise = self.rng.normal(0, 0.01)
        return 51.5074 + lat_noise, -0.1278 + lon_noise
    
    def load_data(self, max_files=15, max_rows_per_file=800):
        """Load and process house price data"""
        csv_files = glob.glob(os.path.join(self.data_dir, "*_link_*.csv"))
        print(f"Found {len(csv_files)} CSV files")
        
        all_data = []
        
        for file_path in csv_files[:max_files]:
            try:
                print(f"Processing {os.path.basename(file_path)}...")
                df = pd.read_csv(file_path, nrows=max_rows_per_file)
                
                # Clean data
                df = df.dropna(subset=['priceper', 'postcode'])
                df = df[df['priceper'] > 0]
                df = df[df['priceper'] < 50000]  # Remove extreme outliers
                
                # Add area name from filename
                area_name = os.path.basename(file_path).replace('_link_26122024.csv', '').replace('_', ' ')
                df['area'] = area_name
                
                all_data.append(df)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        if all_data:
            self.df = pd.concat(all_data, ignore_index=True)
            
            # Add estimated coordinates
            print("Adding coordinate estimates...")
            coords = [self.estimate_coordinates(pc) for pc in self.df['postcode']]
            self.df['lat'] = [c[0] for c in coords]
            self.df['lon'] = [c[1] for c in coords]
            
            # Remove rows with no coordinates
            self.df = self.df.dropna(subset=['lat', 'lon'])
            
            print(f"Loaded {len(self.df)} records with coordinates")
            return self.df
        
        return pd.DataFrame()
    
    def create_app(self):
        """Create Dash application"""
        app = dash.Dash(__name__)
        
        # Load data
        if self.df is None:
            self.load_data()
        
        if self.df.empty:
            app.layout = html.Div([
                html.H1("UK House Price Heatmap"),
                html.P("No data available. Please check your data directory.")
            ])
            return app
        
        # Calculate statistics
        stats = {
            'total_records': len(self.df),
            'avg_price': self.df['priceper'].mean(),
            'min_price': self.df['priceper'].min(),
            'max_price': self.df['priceper'].max(),
            'areas': self.df['area'].nunique()
        }
        
        # Define common styles
        STAT_BOX_STYLE = {
            'textAlign': 'center', 
            'padding': '20px', 
            'border': '1px solid #ddd', 
            'borderRadius': '5px', 
            'margin': '10px',
            'backgroundColor': 'white',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'flex': '1'
        }
        
        app.layout = html.Div([
            html.Div([
                html.H1("London House Price per sqm Interactive Heatmap", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
                
                # Statistics row
                html.Div([
                    html.Div([
                        html.H3(f"{stats['total_records']:,}", style={'margin': '0', 'color': '#3498db'}),
                        html.P("Total Properties", style={'margin': '0', 'fontSize': '14px'})
                    ], style=STAT_BOX_STYLE),
                    
                    html.Div([
                        html.H3(f"£{stats['avg_price']:.0f}", style={'margin': '0', 'color': '#e74c3c'}),
                        html.P("Avg Price/sqm", style={'margin': '0', 'fontSize': '14px'})
                    ], style=STAT_BOX_STYLE),
                    
                    html.Div([
                        html.H3(f"£{stats['min_price']:.0f} - £{stats['max_price']:.0f}", style={'margin': '0', 'color': '#f39c12'}),
                        html.P("Price Range", style={'margin': '0', 'fontSize': '14px'})
                    ], style=STAT_BOX_STYLE),
                    
                    html.Div([
                        html.H3(f"{stats['areas']}", style={'margin': '0', 'color': '#27ae60'}),
                        html.P("Areas Covered", style={'margin': '0', 'fontSize': '14px'})
                    ], style=STAT_BOX_STYLE)
                    
                ], style={
                    'display': 'flex', 
                    'justifyContent': 'space-between', 
                    'marginBottom': '30px',
                    'flexWrap': 'wrap',
                    'gap': '10px'
                }),
                
                # Controls
                html.Div([
                    html.Div([
                        html.Label("Select Areas:", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='area-dropdown',
                            options=[{'label': area, 'value': area} for area in sorted(self.df['area'].unique())],
                            value=sorted(self.df['area'].unique())[:10],  # Select first 10 areas
                            multi=True,
                            style={'marginBottom': '10px'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%', 'verticalAlign': 'top'}),
                    
                    html.Div([
                        html.Label("Price Range (£/sqm):", style={'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                        dcc.RangeSlider(
                            id='price-range-slider',
                            min=self.df['priceper'].min(),
                            max=self.df['priceper'].max(),
                            value=[self.df['priceper'].quantile(0.1), self.df['priceper'].quantile(0.9)],
                            marks={
                                int(self.df['priceper'].min()): f"£{self.df['priceper'].min():.0f}",
                                int(self.df['priceper'].quantile(0.25)): f"£{self.df['priceper'].quantile(0.25):.0f}",
                                int(self.df['priceper'].quantile(0.5)): f"£{self.df['priceper'].quantile(0.5):.0f}",
                                int(self.df['priceper'].quantile(0.75)): f"£{self.df['priceper'].quantile(0.75):.0f}",
                                int(self.df['priceper'].max()): f"£{self.df['priceper'].max():.0f}"
                            },
                            tooltip={"placement": "bottom", "always_visible": True}
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'})
                ], style={'marginBottom': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
                
                # Map
                dcc.Graph(id='price-heatmap', style={'height': '600px', 'marginBottom': '30px'}),
                
                # Additional charts
                html.Div([
                    html.Div([
                        dcc.Graph(id='price-distribution')
                    ], style={'width': '50%', 'display': 'inline-block', 'paddingRight': '10px'}),
                    
                    html.Div([
                        dcc.Graph(id='area-comparison')
                    ], style={'width': '50%', 'display': 'inline-block', 'paddingLeft': '10px'})
                ])
                
            ], style={'padding': '20px', 'maxWidth': '1200px', 'margin': '0 auto'})
        ])
        
        @app.callback(
            [Output('price-heatmap', 'figure'),
             Output('price-distribution', 'figure'),
             Output('area-comparison', 'figure')],
            [Input('area-dropdown', 'value'),
             Input('price-range-slider', 'value')]
        )
        def update_charts(selected_areas, price_range):
            # Filter data
            filtered_df = self.df[
                (self.df['area'].isin(selected_areas)) &
                (self.df['priceper'] >= price_range[0]) &
                (self.df['priceper'] <= price_range[1])
            ]
            
            if filtered_df.empty:
                empty_fig = go.Figure()
                empty_fig.add_annotation(text="No data available for selected filters", 
                                       xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
                return empty_fig, empty_fig, empty_fig
            
            # Create heatmap
            heatmap_fig = go.Figure(data=go.Scattermap(
                lat=filtered_df['lat'],
                lon=filtered_df['lon'],
                mode='markers',
                marker={
                    'size': 8,
                    'color': filtered_df['priceper'],
                    'colorscale': 'Viridis',
                    'showscale': True,
                    'colorbar': {'title': "Price per sqm (£)"},
                    'opacity': 0.7
                },
                text=[f"Area: {area}<br>Postcode: {pc}<br>Price: £{price:.0f}/sqm<br>Year: {year}" 
                      for area, pc, price, year in zip(filtered_df['area'], filtered_df['postcode'], 
                                                      filtered_df['priceper'], filtered_df['year'])],
                hovertemplate='%{text}<extra></extra>'
            ))
            
            heatmap_fig.update_layout(
                map={
                    'style': 'open-street-map',
                    'center': {'lat': 51.5, 'lon': -0.1},
                    'zoom': 8
                },
                title="London House Prices per sqm Heatmap",
                height=600,
                margin={'t': 50, 'b': 0, 'l': 0, 'r': 0}
            )
            
            # Price distribution
            dist_fig = px.histogram(
                filtered_df, 
                x='priceper', 
                nbins=50,
                title="Price per sqm Distribution",
                labels={'priceper': 'Price per sqm (£)', 'count': 'Number of Properties'}
            )
            dist_fig.update_layout(height=400)
            
            # Area comparison
            area_stats = filtered_df.groupby('area')['priceper'].agg(['mean', 'count']).reset_index()
            area_stats = area_stats[area_stats['count'] >= 10]  # Only areas with sufficient data
            area_stats = area_stats.sort_values('mean', ascending=True).tail(15)  # Top 15 areas
            
            area_fig = px.bar(
                area_stats, 
                x='mean', 
                y='area',
                orientation='h',
                title="Average Price per sqm by Area (Top 15)",
                labels={'mean': 'Average Price per sqm (£)', 'area': 'Area'}
            )
            area_fig.update_layout(height=400)
            
            return heatmap_fig, dist_fig, area_fig
        
        return app

if __name__ == "__main__":
    dashboard = UKHousePriceDashboard()
    app = dashboard.create_app()
    app.run(debug=True, host='0.0.0.0', port=8050)
