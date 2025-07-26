import pandas as pd
import requests
import zipfile
import os
from typing import Tuple, Optional
import pickle

class UKPostcodeDataset:
    """
    Download and use pre-built UK postcode datasets
    """
    
    def __init__(self, data_dir="postcode_data"):
        self.data_dir = data_dir
        self.postcode_df = None
        self.postcode_dict = {}
        self.cache_file = "postcode_lookup.pkl"
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def download_ons_postcode_data(self):
        """
        Download the ONS (Office for National Statistics) postcode dataset
        This is the official UK government postcode data - free and comprehensive
        """
        print("Downloading ONS UK postcode dataset...")
        
        # ONS Postcode Directory - this is a large file (~100MB)
        url = "https://www.arcgis.com/sharing/rest/content/items/8f12151bddca4acea96bab7ed710b90b/data"
        
        zip_path = os.path.join(self.data_dir, "ons_postcodes.zip")
        
        try:
            print("Downloading postcode data (this may take a few minutes)...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Extracting postcode data...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_dir)
            
            # Clean up zip file
            os.remove(zip_path)
            print("ONS postcode data downloaded successfully!")
            
        except Exception as e:
            print("Error downloading ONS data: {}".format(e))
            return False
        
        return True
    
    def download_doogal_postcode_data(self):
        """
        Download a smaller, cleaner postcode dataset from Doogal
        This is more manageable and includes lat/long coordinates
        """
        print("Downloading Doogal UK postcode dataset...")
        
        # Doogal UK postcodes - smaller, cleaner dataset
        url = "https://www.doogal.co.uk/files/postcodes.zip"
        
        zip_path = os.path.join(self.data_dir, "doogal_postcodes.zip")
        csv_path = os.path.join(self.data_dir, "postcodes.csv")
        
        try:
            print("Downloading postcode data...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Extracting postcode data...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_dir)
            
            # Clean up zip file
            os.remove(zip_path)
            
            # Check if CSV exists
            if os.path.exists(csv_path):
                print("Doogal postcode data downloaded successfully!")
                return True
            else:
                print("CSV file not found after extraction")
                return False
                
        except Exception as e:
            print("Error downloading Doogal data: {}".format(e))
            return False
    
    def load_postcode_data(self, force_download=False):
        """
        Load postcode data from local file or download if needed
        """
        csv_path = os.path.join(self.data_dir, "postcodes.csv")
        
        # Check if we have a cached lookup
        if os.path.exists(self.cache_file) and not force_download:
            print("Loading cached postcode lookup...")
            try:
                with open(self.cache_file, 'rb') as f:
                    self.postcode_dict = pickle.load(f)
                print("Loaded {} postcodes from cache".format(len(self.postcode_dict)))
                return True
            except Exception as e:
                print("Error loading cache: {}".format(e))
        
        # Check if CSV exists locally
        if not os.path.exists(csv_path) or force_download:
            print("Postcode data not found locally, downloading...")
            if not self.download_doogal_postcode_data():
                print("Failed to download postcode data")
                return False
        
        # Load CSV data
        try:
            print("Loading postcode CSV data...")
            self.postcode_df = pd.read_csv(csv_path)
            
            # Check column names (Doogal format)
            expected_cols = ['Postcode', 'Latitude', 'Longitude']
            if all(col in self.postcode_df.columns for col in expected_cols):
                print("Loaded {} postcodes from CSV".format(len(self.postcode_df)))
                
                # Create lookup dictionary for faster access
                print("Creating postcode lookup dictionary...")
                self.postcode_dict = {}
                for _, row in self.postcode_df.iterrows():
                    postcode = row['Postcode'].strip().upper()
                    lat = row['Latitude']
                    lon = row['Longitude']
                    if pd.notna(lat) and pd.notna(lon):
                        self.postcode_dict[postcode] = (float(lat), float(lon))
                
                # Save to cache
                print("Saving postcode lookup to cache...")
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.postcode_dict, f)
                
                print("Created lookup for {} postcodes".format(len(self.postcode_dict)))
                return True
            else:
                print("Unexpected CSV format. Columns: {}".format(list(self.postcode_df.columns)))
                return False
                
        except Exception as e:
            print("Error loading CSV data: {}".format(e))
            return False
    
    def get_coordinates(self, postcode: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a postcode from the local dataset
        """
        if not postcode:
            return None
        
        # Clean postcode - remove spaces and make uppercase
        clean_postcode = postcode.strip().upper().replace(' ', '')
        
        # Try exact match first
        if clean_postcode in self.postcode_dict:
            return self.postcode_dict[clean_postcode]
        
        # Try with space in different positions for UK postcode format
        if len(clean_postcode) >= 5:
            # Try different space positions (e.g., "N29QL" -> "N2 9QL", "N29 QL")
            variants = [
                clean_postcode[:-3] + ' ' + clean_postcode[-3:],  # Most common format
                clean_postcode[:-2] + ' ' + clean_postcode[-2:],  # Alternative format
            ]
            
            for variant in variants:
                if variant in self.postcode_dict:
                    return self.postcode_dict[variant]
        
        return None
    
    def geocode_dataframe(self, df: pd.DataFrame, postcode_column: str = 'postcode') -> pd.DataFrame:
        """
        Add lat/lon coordinates to a dataframe using the local postcode dataset
        """
        if not self.postcode_dict:
            print("Postcode data not loaded. Call load_postcode_data() first.")
            return df
        
        print("Geocoding postcodes from column '{}'...".format(postcode_column))
        
        coords_list = []
        successful = 0
        
        for postcode in df[postcode_column]:
            coords = self.get_coordinates(postcode)
            if coords:
                coords_list.append(coords)
                successful += 1
            else:
                coords_list.append((None, None))
        
        df['lat'] = [c[0] for c in coords_list]
        df['lon'] = [c[1] for c in coords_list]
        
        print("Successfully geocoded {}/{} records ({:.1f}%)".format(successful, len(df), successful/len(df)*100))
        
        return df


# Test the dataset loader
if __name__ == "__main__":
    geocoder = UKPostcodeDataset()
    
    # Load postcode data
    if geocoder.load_postcode_data():
        # Test some postcodes
        test_postcodes = ["N2 9QL", "SW1A 1AA", "EC1A 1BB", "W1A 0AX", "M1 1AA"]
        
        print("\nTesting postcodes:")
        for pc in test_postcodes:
            coords = geocoder.get_coordinates(pc)
            print("{}: {}".format(pc, coords))
    else:
        print("Failed to load postcode data")
