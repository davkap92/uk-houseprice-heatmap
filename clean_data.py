import os
import glob

def clean_data_folder():
    """Remove CSV files that are not London or Greater London belt areas"""
    
    # London boroughs and Greater London areas to keep
    london_areas = {
        # Inner London Boroughs
        'City_of_London',
        'Camden',
        'Greenwich',
        'Hackney',
        'Hammersmith_and_Fulham',
        'Islington',
        'Kensington_and_Chelsea',
        'Lambeth',
        'Lewisham',
        'Southwark',
        'Tower_Hamlets',
        'Wandsworth',
        'Westminster',
        
        # Outer London Boroughs
        'Barking_and_Dagenham',
        'Barnet',
        'Bexley',
        'Brent',
        'Bromley',
        'Croydon',
        'Ealing',
        'Enfield',
        'Haringey',
        'Harrow',
        'Havering',
        'Hillingdon',
        'Hounslow',
        'Kingston_upon_Thames',
        'Merton',
        'Newham',
        'Redbridge',
        'Richmond_upon_Thames',
        'Sutton',
        'Waltham_Forest',
        
        # Greater London Belt / Commuter Areas
        'Dartford',           # Kent - close to London
        'Gravesham',          # Kent - close to London
        'Swale',              # Kent
        'Tandridge',          # Surrey - close to London
        'Elmbridge',          # Surrey - close to London
        'Epsom_and_Ewell',    # Surrey - close to London
        'Guildford',          # Surrey - commuter area
        'Mole_Valley',        # Surrey - close to London
        'Reigate_and_Banstead', # Surrey - close to London
        'Runnymede',          # Surrey - close to London
        'Spelthorne',         # Surrey - close to London
        'Surrey_Heath',       # Surrey - close to London
        'Waverley',           # Surrey - commuter area
        'Woking',             # Surrey - commuter area
        'Hertsmere',          # Hertfordshire - close to London
        'Watford',            # Hertfordshire - close to London
        'Three_Rivers',       # Hertfordshire - close to London
        'Welwyn_Hatfield',    # Hertfordshire - close to London
        'St_Albans',          # Hertfordshire - commuter area
        'Dacorum',            # Hertfordshire - commuter area
        'East_Hertfordshire', # Hertfordshire - commuter area
        'North_Hertfordshire', # Hertfordshire - commuter area
        'Stevenage',          # Hertfordshire - commuter area
        'Broxbourne',         # Hertfordshire - close to London
        'Epping_Forest',      # Essex - close to London
        'Harlow',             # Essex - close to London
        'Uttlesford',         # Essex - commuter area
        'Brentwood',          # Essex - commuter area
        'Chelmsford',         # Essex - commuter area
        'Basildon',           # Essex - commuter area
        'Castle_Point',       # Essex - commuter area
        'Rochford',           # Essex - commuter area
        'Maldon',             # Essex - commuter area
        'Thurrock',           # Essex - close to London
        'Slough',             # Berkshire - close to London
        'Windsor_and_Maidenhead', # Berkshire - close to London
        'Bracknell_Forest',   # Berkshire - commuter area
        'Reading',            # Berkshire - commuter area
        'Wokingham',          # Berkshire - commuter area
        'West_Berkshire',     # Berkshire - commuter area
        'Crawley',            # West Sussex - commuter area
        'Mid_Sussex',         # West Sussex - commuter area
        'Horsham',            # West Sussex - commuter area
        'Tunbridge_Wells',    # Kent - commuter area
        'Tonbridge_and_Malling', # Kent - commuter area
        'Sevenoaks',          # Kent - commuter area
        'Luton',              # Bedfordshire - commuter area
        'Milton_Keynes',      # Buckinghamshire - commuter area
    }
    
    data_dir = "data"
    csv_files = glob.glob(os.path.join(data_dir, "*_link_*.csv"))
    
    files_to_delete = []
    files_to_keep = []
    
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        area_name = filename.replace('_link_26122024.csv', '')
        
        if area_name in london_areas:
            files_to_keep.append(filename)
        else:
            files_to_delete.append(file_path)
    
    print(f"Found {len(csv_files)} total CSV files")
    print(f"Will keep {len(files_to_keep)} London/Greater London files:")
    for f in sorted(files_to_keep):
        print(f"  ✓ {f}")
    
    print(f"\nWill delete {len(files_to_delete)} non-London files:")
    for f in sorted(files_to_delete):
        filename = os.path.basename(f)
        print(f"  ✗ {filename}")
    
    # Ask for confirmation
    response = input(f"\nDo you want to delete {len(files_to_delete)} files? (y/N): ")
    
    if response.lower() == 'y':
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
                print(f"Deleted: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        print(f"\n✅ Successfully deleted {deleted_count} files")
        print(f"✅ Kept {len(files_to_keep)} London/Greater London files")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    clean_data_folder()
