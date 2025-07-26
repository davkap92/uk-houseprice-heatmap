import pandas as pd
import requests
import json
import os
import pickle
from typing import Tuple, Optional
import time

class UKPostcodeGeocoder:
    """
    A class to geocode UK postcodes using various APIs and datasets
    """
    
    def __init__(self, cache_file="postcode_coords_cache.pkl"):
        self.cache_file = cache_file
        self.postcode_cache = {}
        self.load_cache()
        
    def load_cache(self):
        """Load cached postcode coordinates"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.postcode_cache = pickle.load(f)
                print(f"Loaded {len(self.postcode_cache)} cached postcode coordinates")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.postcode_cache = {}
    
    def save_cache(self):
        """Save postcode coordinates to cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.postcode_cache, f)
            print(f"Saved {len(self.postcode_cache)} postcode coordinates to cache")
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def geocode_postcode_api(self, postcode: str) -> Optional[Tuple[float, float]]:
        """
        Geocode a UK postcode using postcodes.io API (free, no rate limits)
        """
        if not postcode:
            return None
            
        # Clean postcode
        clean_postcode = postcode.strip().upper().replace(' ', '')
        
        try:
            # Use postcodes.io - free UK postcode API
            url = f"https://api.postcodes.io/postcodes/{clean_postcode}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 200 and 'result' in data:
                    result = data['result']
                    lat = result.get('latitude')
                    lon = result.get('longitude')
                    if lat and lon:
                        return float(lat), float(lon)
            
        except Exception as e:
            print(f"Error geocoding {postcode}: {e}")
        
        return None
    
    def geocode_postcode_batch(self, postcodes: list) -> dict:
        """
        Geocode multiple postcodes in batch (max 100 at a time for postcodes.io)
        """
        results = {}
        
        # Process in batches of 100
        for i in range(0, len(postcodes), 100):
            batch = postcodes[i:i+100]
            clean_batch = [pc.strip().upper().replace(' ', '') for pc in batch if pc]
            
            try:
                url = "https://api.postcodes.io/postcodes"
                payload = {"postcodes": clean_batch}
                response = requests.post(url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 200 and 'result' in data:
                        for idx, result in enumerate(data['result']):
                            original_postcode = batch[idx] if idx < len(batch) else None
                            if original_postcode and result and 'result' in result:
                                res = result['result']
                                if res:
                                    lat = res.get('latitude')
                                    lon = res.get('longitude')
                                    if lat and lon:
                                        results[original_postcode] = (float(lat), float(lon))
                
                # Be nice to the API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in batch geocoding: {e}")
                continue
        
        return results
    
    def get_coordinates(self, postcode: str) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a postcode, using cache first, then API
        """
        if not postcode:
            return None
            
        # Check cache first
        if postcode in self.postcode_cache:
            return self.postcode_cache[postcode]
        
        # Try API
        coords = self.geocode_postcode_api(postcode)
        if coords:
            self.postcode_cache[postcode] = coords
            return coords
        
        return None
    
    def geocode_dataframe(self, df: pd.DataFrame, postcode_column: str = 'postcode', 
                         batch_size: int = 1000) -> pd.DataFrame:
        """
        Geocode all postcodes in a dataframe
        """
        print(f"Geocoding postcodes from column '{postcode_column}'...")
        
        # Get unique postcodes that aren't already cached
        unique_postcodes = df[postcode_column].dropna().unique()
        uncached_postcodes = [pc for pc in unique_postcodes if pc not in self.postcode_cache]
        
        print(f"Found {len(unique_postcodes)} unique postcodes, {len(uncached_postcodes)} need geocoding")
        
        if uncached_postcodes:
            # Process in batches
            for i in range(0, len(uncached_postcodes), batch_size):
                batch = uncached_postcodes[i:i+batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(len(uncached_postcodes) + batch_size - 1)//batch_size}")
                
                batch_results = self.geocode_postcode_batch(batch)
                self.postcode_cache.update(batch_results)
                
                # Save cache periodically
                if (i // batch_size + 1) % 5 == 0:
                    self.save_cache()
        
        # Apply coordinates to dataframe
        coords_list = []
        for postcode in df[postcode_column]:
            coords = self.postcode_cache.get(postcode)
            if coords:
                coords_list.append(coords)
            else:
                coords_list.append((None, None))
        
        df['lat'] = [c[0] for c in coords_list]
        df['lon'] = [c[1] for c in coords_list]
        
        # Save final cache
        self.save_cache()
        
        successful_geocodes = df[['lat', 'lon']].dropna().shape[0]
        print(f"Successfully geocoded {successful_geocodes}/{len(df)} records")
        
        return df

# Test the geocoder
if __name__ == "__main__":
    geocoder = UKPostcodeGeocoder()
    
    # Test some postcodes
    test_postcodes = ["N2 9QL", "SW1A 1AA", "EC1A 1BB", "W1A 0AX"]
    
    print("Testing individual postcodes:")
    for pc in test_postcodes:
        coords = geocoder.get_coordinates(pc)
        print(f"{pc}: {coords}")
    
    # Test batch geocoding
    print("\nTesting batch geocoding:")
    batch_results = geocoder.geocode_postcode_batch(test_postcodes)
    for pc, coords in batch_results.items():
        print(f"{pc}: {coords}")
