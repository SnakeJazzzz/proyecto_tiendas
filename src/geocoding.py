"""
Improved geocoding module with better address handling for Mexican locations
"""

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
import json
import os
import time

class GeocodingManager:
    def __init__(self, cache_file='geocoding_cache.json'):
        """
        Initialize geocoding manager with cache support
        
        Parameters:
        -----------
        cache_file : str, optional
            Path to the geocoding cache file (default: 'geocoding_cache.json')
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.geolocator = Nominatim(user_agent="proyecto_tiendas")
        self.geocode = RateLimiter(
            self.geolocator.geocode, 
            min_delay_seconds=1.5,  # Increased to avoid hitting rate limits
            error_wait_seconds=3,
            max_retries=3
        )
        
        # Special locations for common cities in Mexico
        # If geocoding fails, we can fallback to these coordinates
        self.fallback_locations = {
            'CIUDAD DE MEXICO': (19.4326, -99.1332),
            'MEXICO CITY': (19.4326, -99.1332),
            'CDMX': (19.4326, -99.1332),
            'GUADALAJARA': (20.6597, -103.3496),
            'MONTERREY': (25.6866, -100.3161),
            'PUEBLA': (19.0414, -98.2063),
            'TIJUANA': (32.5149, -117.0382),
            'LEON': (21.1218, -101.6741),
            'JUAREZ': (31.6904, -106.4245),
            'CULIACAN': (24.8087, -107.3940),
            'MERIDA': (20.9674, -89.5926),
            'AGUASCALIENTES': (21.8818, -102.2916),
            'ACAPULCO': (16.8531, -99.8237),
            'HERMOSILLO': (29.0729, -110.9559),
            'QUERETARO': (20.5888, -100.3899),
            'MORELIA': (19.7060, -101.1950),
            'VERACRUZ': (19.1738, -96.1342),
            'CANCUN': (21.1619, -86.8515),
            'PACHUCA': (20.1222, -98.7324),
            'TOLUCA': (19.2826, -99.6557),
            'TAMPICO': (22.2331, -97.8614),
            'VILLAHERMOSA': (17.9892, -92.9282),
            'CUERNAVACA': (18.9242, -99.2216),
            'CHIHUAHUA': (28.6353, -106.0889),
            'OAXACA': (17.0732, -96.7266),
            'TUXTLA': (16.7530, -93.1179),
            'DURANGO': (24.0277, -104.6532),
            'SAN LUIS POTOSI': (22.1565, -100.9855),
            'MAZATLAN': (23.2494, -106.4111),
            'TEPIC': (21.5046, -104.8949),
            'CAMPECHE': (19.8301, -90.5349),
            'COLIMA': (19.2433, -103.7247),
            'LA PAZ': (24.1426, -110.3127),
            'ZACATECAS': (22.7709, -102.5832),
            'TLAXCALA': (19.3189, -98.2383),
            'CELAYA': (20.5279, -100.8133),
            'IRAPUATO': (20.6786, -101.3544),
            'MONCLOVA': (26.9082, -101.4212),
            'PARRAL': (26.9295, -105.6663),
            'ENSENADA': (31.8423, -116.6079),
            'MEXICALI': (32.6245, -115.4522),
            'SALTILLO': (25.4267, -101.0029),
            'TAPACHULA': (14.9019, -92.2572),
            'URUAPAN': (19.4096, -102.0567)
        }
    
    def _load_cache(self):
        """Load geocoding cache from JSON file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                print(f"Warning: Could not load cache from {self.cache_file}. Starting with empty cache.")
                return {}
        else:
            return {}
    
    def _save_cache(self):
        """Save geocoding cache to JSON file"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def extract_city_from_name(self, store_name):
        """
        Try to extract a city name from the store name
        
        Parameters:
        -----------
        store_name : str
            Name of the store
            
        Returns:
        --------
        str or None
            Extracted city name or None if not found
        """
        # Common patterns in store names: "CITY CENTRO", "CITY PLAZA", etc.
        store_parts = store_name.upper().split()
        
        # Check against known city names
        for city in self.fallback_locations.keys():
            city_parts = city.split()
            if any(part in store_parts for part in city_parts):
                return city
        
        return None
    
    def geocode_address(self, address, store_name=None, state=None, city=None, timeout=10):
        """
        Geocode an address with caching and fallbacks
        
        Parameters:
        -----------
        address : str
            Full address to geocode
        store_name : str, optional
            Name of the store (for fallback city extraction)
        state : str, optional
            State name (for fallback)
        city : str, optional
            City name (for fallback)
        timeout : int, optional
            Timeout in seconds (default: 10)
            
        Returns:
        --------
        tuple
            (latitude, longitude) or (None, None) if geocoding failed
        """
        # Clean and standardize address
        query = address.strip()
        cache_key = query
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]['lat'], self.cache[cache_key]['lon']
        
        # Not in cache, perform geocoding
        try:
            location = self.geocode(query, timeout=timeout)
            if location:
                lat, lon = location.latitude, location.longitude
                # Add to cache
                self.cache[cache_key] = {'lat': lat, 'lon': lon}
                # Save cache every few requests to avoid losing data on crashes
                if len(self.cache) % 10 == 0:
                    self._save_cache()
                return lat, lon
            else:
                # Try with city + state if available
                if city and state:
                    query = f"{city}, {state}, México"
                    # Check if this query is in cache
                    if query in self.cache:
                        lat, lon = self.cache[query]['lat'], self.cache[query]['lon']
                        # Also cache the original query
                        self.cache[cache_key] = {'lat': lat, 'lon': lon}
                        return lat, lon
                    
                    # Try geocoding with city and state
                    location = self.geocode(query, timeout=timeout)
                    if location:
                        lat, lon = location.latitude, location.longitude
                        # Add to cache
                        self.cache[cache_key] = {'lat': lat, 'lon': lon}
                        self.cache[query] = {'lat': lat, 'lon': lon}
                        # Save cache every few requests to avoid losing data on crashes
                        if len(self.cache) % 10 == 0:
                            self._save_cache()
                        return lat, lon
                
                # Try extracting city from store name as last resort
                if store_name:
                    city_name = self.extract_city_from_name(store_name)
                    if city_name and city_name in self.fallback_locations:
                        lat, lon = self.fallback_locations[city_name]
                        # Add to cache
                        self.cache[cache_key] = {'lat': lat, 'lon': lon}
                        # Save cache every few requests to avoid losing data on crashes
                        if len(self.cache) % 10 == 0:
                            self._save_cache()
                        return lat, lon
                
                # Cache negative results too to avoid repeated failed queries
                self.cache[cache_key] = {'lat': None, 'lon': None}
                return None, None
        except Exception as e:
            print(f"Geocoding error for '{query}': {str(e)}")
            return None, None
    
    def geocode_dataframe(self, df):
        """
        Geocode all addresses in a DataFrame with improved fallbacks
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with address information
            
        Returns:
        --------
        pd.DataFrame
            DataFrame with added 'latitud' and 'longitud' columns
        """
        # Create a copy of the dataframe to avoid modifying the original
        result_df = df.copy()
        
        # Create empty columns for coordinates
        result_df['latitud'] = None
        result_df['longitud'] = None
        
        # Counter for progress reporting
        total = len(result_df)
        print(f"Geocoding {total} addresses...")
        
        # Track statistics
        successful = 0
        cached = 0
        fallback = 0
        failed = 0
        
        # Geocode each address
        for i, row in result_df.iterrows():
            # Build the full address string using all available information
            address_parts = []
            
            # Add address components if they exist
            if pd.notna(row.get('Calle')):
                address_parts.append(str(row['Calle']).strip())
            
            if pd.notna(row.get('Colonia')):
                address_parts.append(str(row['Colonia']).strip())
            
            if pd.notna(row.get('Municipio')):
                address_parts.append(str(row['Municipio']).strip())
            
            if pd.notna(row.get('Ciudad')):
                address_parts.append(str(row['Ciudad']).strip())
            
            if pd.notna(row.get('Estado')):
                address_parts.append(str(row['Estado']).strip())
            
            if pd.notna(row.get('CP')):
                address_parts.append(str(row['CP']).strip())
            
            # Add Mexico at the end to improve geocoding accuracy
            address_parts.append('México')
            
            # Join all parts with commas
            full_address = ', '.join(address_parts)
            
            # Get store name, city and state for fallbacks
            store_name = row.get('Sucursal', '')
            city = row.get('Ciudad', '')
            state = row.get('Estado', '')
            
            # Check if this address is already in cache
            cache_key = full_address.strip()
            if cache_key in self.cache and self.cache[cache_key]['lat'] is not None:
                result_df.at[i, 'latitud'] = self.cache[cache_key]['lat']
                result_df.at[i, 'longitud'] = self.cache[cache_key]['lon']
                cached += 1
            else:
                # Geocode the address
                lat, lon = self.geocode_address(full_address, store_name, state, city)
                
                # If geocoding failed, try with just city and state
                if lat is None and (city or state):
                    fallback_query = f"{city}, {state}, México".strip(', ')
                    lat, lon = self.geocode_address(fallback_query)
                    if lat is not None:
                        fallback += 1
                else:
                    successful += 1
                
                # If still failed, try using the store name for common city names
                if lat is None and store_name:
                    city_name = self.extract_city_from_name(store_name)
                    if city_name and city_name in self.fallback_locations:
                        lat, lon = self.fallback_locations[city_name]
                        fallback += 1
                
                # Store the results
                result_df.at[i, 'latitud'] = lat
                result_df.at[i, 'longitud'] = lon
                
                if lat is None:
                    failed += 1
            
            # Report progress every 10 stores
            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"Geocoded {i + 1}/{total} addresses ({(i + 1) / total * 100:.1f}%)")
        
        # Save the final cache
        self._save_cache()
        print(f"Geocoding completed. Cache saved to {self.cache_file}")
        print(f"Statistics: {successful} successful, {cached} from cache, {fallback} used fallback, {failed} failed")
        
        return result_df