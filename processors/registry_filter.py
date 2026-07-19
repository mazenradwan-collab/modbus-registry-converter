"""Registry filter for filtering registers before conversion"""

import pandas as pd
from typing import List, Dict, Set


class RegistryFilter:
    """Filter registers based on various criteria"""
    
    # Define common register categories
    REGISTER_CATEGORIES = {
        'voltage': {
            'keywords': ['volt', 'v', 'voltage', 'vac', 'vdc'],
            'description': 'Voltage registers'
        },
        'current': {
            'keywords': ['current', 'amp', 'a', 'amps', 'ampere', 'amperage'],
            'description': 'Current registers'
        },
        'frequency': {
            'keywords': ['freq', 'frequency', 'hz', 'hertz'],
            'description': 'Frequency registers'
        },
        'power': {
            'keywords': ['power', 'kw', 'mw', 'w', 'watt', 'power factor', 'pf'],
            'description': 'Power registers'
        },
        'energy': {
            'keywords': ['energy', 'kwh', 'mwh', 'wh', 'joule'],
            'description': 'Energy registers'
        },
        'temperature': {
            'keywords': ['temp', 'temperature', 'celsius', 'c', 'fahrenheit', 'f'],
            'description': 'Temperature registers'
        },
        'pressure': {
            'keywords': ['pressure', 'psi', 'bar', 'pascal', 'pa'],
            'description': 'Pressure registers'
        },
        'flow': {
            'keywords': ['flow', 'flowrate', 'gpm', 'lpm', 'l/min'],
            'description': 'Flow registers'
        },
        'status': {
            'keywords': ['status', 'state', 'condition', 'flag', 'alarm', 'fault', 'error'],
            'description': 'Status and alarm registers'
        },
        'control': {
            'keywords': ['control', 'command', 'setpoint', 'set_point', 'sp'],
            'description': 'Control and command registers'
        }
    }
    
    def __init__(self):
        self.available_categories = set(self.REGISTER_CATEGORIES.keys())
        self.selected_categories = set()
        self.excluded_keywords = set()
        self.included_keywords = set()
    
    def select_categories(self, categories: List[str]):
        """Select categories to include in filtering"""
        valid_categories = [cat.lower() for cat in categories if cat.lower() in self.available_categories]
        self.selected_categories = set(valid_categories)
        return valid_categories
    
    def add_excluded_keywords(self, keywords: List[str]):
        """Add keywords to exclude from filtering"""
        self.excluded_keywords.update([kw.lower().strip() for kw in keywords])
    
    def add_included_keywords(self, keywords: List[str]):
        """Add keywords to include in filtering"""
        self.included_keywords.update([kw.lower().strip() for kw in keywords])
    
    def get_available_categories(self) -> Dict[str, Dict]:
        """Get all available filter categories"""
        return self.REGISTER_CATEGORIES.copy()
    
    def get_category_description(self, category: str) -> str:
        """Get description of a category"""
        if category.lower() in self.REGISTER_CATEGORIES:
            return self.REGISTER_CATEGORIES[category.lower()]['description']
        return "Unknown category"
    
    def filter_records(self, records: List[Dict], category_mode='include') -> tuple:
        """
        Filter records based on selected categories and keywords
        
        Args:
            records: List of register records
            category_mode: 'include' to include selected categories, 'exclude' to exclude them
        
        Returns:
            Tuple of (filtered_records, filter_report)
        """
        if not records:
            return [], self._generate_report(records, [])
        
        filtered_indices = []
        
        for idx, record in enumerate(records):
            if self._matches_filters(record, category_mode):
                filtered_indices.append(idx)
        
        filtered_records = [records[i] for i in filtered_indices]
        report = self._generate_report(records, filtered_indices)
        
        return filtered_records, report
    
    def _matches_filters(self, record: Dict, category_mode: str = 'include') -> bool:
        """Check if record matches filter criteria"""
        
        # Get register name and display name for matching
        reg_name = str(record.get('RegisterName', '')).lower()
        display_name = str(record.get('DisplayName', '')).lower()
        unit = str(record.get('Unit', '')).lower()
        
        text_to_search = f"{reg_name} {display_name} {unit}"
        
        # Check excluded keywords first
        if self.excluded_keywords:
            for keyword in self.excluded_keywords:
                if keyword in text_to_search:
                    return False
        
        # If included keywords are specified, must match at least one
        if self.included_keywords:
            match_found = False
            for keyword in self.included_keywords:
                if keyword in text_to_search:
                    match_found = True
                    break
            if not match_found:
                return False
        
        # Check category filters
        if not self.selected_categories:
            return True
        
        category_match = self._matches_any_category(text_to_search)
        
        if category_mode == 'include':
            return category_match
        else:  # exclude mode
            return not category_match
    
    def _matches_any_category(self, text: str) -> bool:
        """Check if text matches any of the selected categories"""
        
        for category in self.selected_categories:
            if category in self.REGISTER_CATEGORIES:
                keywords = self.REGISTER_CATEGORIES[category]['keywords']
                for keyword in keywords:
                    if keyword in text:
                        return True
        
        return False
    
    def _generate_report(self, original_records: List[Dict], filtered_indices: List[int]) -> Dict:
        """Generate filtering report"""
        
        report = {
            'total_records': len(original_records),
            'filtered_records': len(filtered_indices),
            'excluded_records': len(original_records) - len(filtered_indices),
            'filter_summary': {
                'selected_categories': list(self.selected_categories),
                'excluded_keywords': list(self.excluded_keywords),
                'included_keywords': list(self.included_keywords),
                'category_mode': 'include'
            },
            'filtered_register_names': []
        }
        
        if original_records:
            report['filtered_register_names'] = [
                original_records[i].get('RegisterName', 'Unknown')
                for i in filtered_indices
            ]
        
        return report


class FilterBuilder:
    """Builder class for creating complex filters"""
    
    def __init__(self):
        self.filter = RegistryFilter()
    
    def with_categories(self, *categories) -> 'FilterBuilder':
        """Add categories to filter"""
        self.filter.select_categories(list(categories))
        return self
    
    def exclude_keywords(self, *keywords) -> 'FilterBuilder':
        """Add keywords to exclude"""
        self.filter.add_excluded_keywords(list(keywords))
        return self
    
    def include_keywords(self, *keywords) -> 'FilterBuilder':
        """Add keywords to include"""
        self.filter.add_included_keywords(list(keywords))
        return self
    
    def build(self) -> RegistryFilter:
        """Build and return the filter"""
        return self.filter


def get_filter_presets() -> Dict[str, Dict]:
    """Get predefined filter presets for common use cases"""
    
    return {
        'power_monitoring': {
            'categories': ['voltage', 'current', 'power', 'frequency'],
            'description': 'Filter for power monitoring registers'
        },
        'energy_metering': {
            'categories': ['voltage', 'current', 'energy', 'power'],
            'description': 'Filter for energy metering registers'
        },
        'hvac_control': {
            'categories': ['temperature', 'pressure', 'flow'],
            'description': 'Filter for HVAC control registers'
        },
        'critical_only': {
            'categories': ['voltage', 'current', 'temperature', 'status'],
            'description': 'Filter for critical parameters only'
        },
        'exclude_status': {
            'categories': [],
            'excluded_keywords': ['status', 'flag', 'alarm', 'error'],
            'description': 'Exclude status and alarm registers'
        },
        'measurements_only': {
            'categories': ['voltage', 'current', 'power', 'energy', 'temperature', 'pressure', 'flow'],
            'description': 'Include only measurement registers'
        }
    }
