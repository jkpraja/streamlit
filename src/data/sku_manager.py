import pandas as pd
from .legend_loader import (
    load_sheet_data,
    save_sheet_data,
    get_sheet_names
)

class SKUManager:
    def __init__(self):
        """Initialize SKU manager."""
        self.available_sheets = get_sheet_names()
        self._load_mappings()

    def _find_state_sheet(self):
        """Find the state sheet name, accounting for different possible names."""
        state_sheet_variants = ['us state', 'US State', 'US STATE', 'us_state', 'USState', 'State']
        for sheet in self.available_sheets:
            if any(variant.lower() == sheet.lower() for variant in state_sheet_variants):
                return sheet
        return None

    def _load_mappings(self):
        """Load SKU and state mappings from legend data."""
        self.sku_mapping = {}
        self.state_mapping = {}
        self.state_name_to_code = {}
        self.valid_state_codes = set()
        
        for sheet_name in self.available_sheets:
            sheet_data = load_sheet_data(sheet_name)
            
            # Load SKU mappings
            if not sheet_data.empty and 'SKU' in sheet_data.columns and 'Merchant SKU' in sheet_data.columns:
                sheet_sku_mapping = dict(zip(sheet_data['Merchant SKU'], sheet_data['SKU']))
                self.sku_mapping.update(sheet_sku_mapping)
        
        # Load state mappings
        state_sheet_name = self._find_state_sheet()
        if state_sheet_name:
            state_sheet = load_sheet_data(state_sheet_name)
            
            if not state_sheet.empty and 'State Code' in state_sheet.columns and 'State Name' in state_sheet.columns:
                # Create mappings from both code and name to code
                codes = state_sheet['State Code'].str.strip()
                names = state_sheet['State Name'].str.strip()
                
                # Store valid state codes
                self.valid_state_codes = set(codes)
                
                # Map state names to codes
                self.state_name_to_code.update(dict(zip(names, codes)))
                # Also map codes to themselves for direct matches
                self.state_name_to_code.update(dict(zip(codes, codes)))

    def get_available_sheets(self):
        """
        Get list of all available sheets in the legend spreadsheet.
        """
        return self.available_sheets

    def get_sheet_data(self, sheet_name):
        """
        Get data from a specific sheet.
        """
        # For state sheet, try to find the correct name
        if sheet_name.lower() == 'us state':
            state_sheet = self._find_state_sheet()
            if state_sheet:
                return load_sheet_data(state_sheet)
        return load_sheet_data(sheet_name)

    def get_valid_states(self):
        """
        Get list of valid state codes from legend.
        """
        return sorted(list(self.valid_state_codes))

    def get_state_names(self):
        """
        Get mapping of state codes to names.
        """
        state_sheet_name = self._find_state_sheet()
        if state_sheet_name:
            state_sheet = load_sheet_data(state_sheet_name)
            if not state_sheet.empty and 'State Code' in state_sheet.columns and 'State Name' in state_sheet.columns:
                return dict(zip(state_sheet['State Code'].str.strip(), state_sheet['State Name'].str.strip()))
        return {}

    def save_sheet_data(self, df, sheet_name):
        """
        Save data to a specific sheet.
        """
        success = save_sheet_data(df, sheet_name)
        if success:
            # Refresh available sheets list and mappings
            self.available_sheets = get_sheet_names()
            self._load_mappings()
        return success

    def map_sku(self, merchant_sku):
        """
        Map a Merchant SKU to its corresponding SKU.
        Returns the mapped SKU if found, otherwise returns the original Merchant SKU.
        """
        return self.sku_mapping.get(merchant_sku, merchant_sku)

    def map_state(self, state):
        """
        Map a state name or code to its corresponding state code.
        Returns the mapped state code if found, otherwise returns None.
        """
        if pd.isna(state):
            return None
        mapped_state = self.state_name_to_code.get(str(state).strip())
        return mapped_state if mapped_state in self.valid_state_codes else None

    def map_skus_in_df(self, df, merchant_sku_col='Merchant SKU', new_sku_col='SKU'):
        """
        Add mapped SKUs to a DataFrame and handle state mapping.
        Returns DataFrame with mapped SKUs and states.
        """
        if merchant_sku_col in df.columns:
            df = df.copy()
            # Map SKUs
            df[new_sku_col] = df[merchant_sku_col].map(self.sku_mapping).fillna(df[merchant_sku_col])
            
            # Map states if state column exists
            if 'Shipping State' in df.columns and self.valid_state_codes:
                # Create new column for mapped states
                df['State Code'] = df['Shipping State'].apply(self.map_state)
                # Filter out rows with unmapped states
                df = df[df['State Code'].notna()]
                # Replace original state column with mapped state codes
                df['Shipping State'] = df['State Code']
                df.drop('State Code', axis=1, inplace=True)
            
            return df
        return df
