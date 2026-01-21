"""
File Detector - Detects which day's challenge from various sources
"""
import re
import json
from typing import Optional, Tuple
from fuzzywuzzy import fuzz


class FileDetector:
    """Detects which day's challenge is being submitted"""
    
    def __init__(self, challenges_path: str = "challenges.json"):
        """Initialize with challenges data"""
        with open(challenges_path, 'r') as f:
            data = json.load(f)
            self.challenges = {item['day']: item for item in data['schedule']}
    
    def detect_day(self, pr_title: str, pr_description: str, 
                   file_paths: list, file_names: list) -> Tuple[Optional[int], str, float]:
        """
        Detect which day's challenge using multiple methods
        
        Args:
            pr_title: PR title
            pr_description: PR description
            file_paths: List of file paths
            file_names: List of file names
            
        Returns:
            Tuple of (day_number, detection_method, confidence)
        """
        # Method 1: PR Title/Description
        day, conf = self._check_pr_text(pr_title, pr_description)
        if day and conf > 0.85:
            return day, "pr_title", conf
        
        # Method 2: Folder Path
        day, conf = self._check_folder_path(file_paths)
        if day and conf > 0.85:
            return day, "folder_path", conf
        
        # Method 3: Contract Name (Direct Match)
        day, conf = self._match_contract_name_exact(file_names)
        if day and conf > 0.85:
            return day, "contract_name_exact", conf
        
        # Method 4: File Name Pattern
        day, conf = self._check_filename_pattern(file_names)
        if day and conf > 0.65:
            return day, "filename_pattern", conf
        
        # Method 5: Contract Name (Fuzzy Match)
        day, conf = self._match_contract_name_fuzzy(file_names)
        if day and conf > 0.60:
            return day, "contract_name_fuzzy", conf
        
        return None, "unknown", 0.0
    
    def _check_pr_text(self, title: str, description: str) -> Tuple[Optional[int], float]:
        """Check PR title and description for day number"""
        text = f"{title} {description}".lower()
        
        # Pattern: day 1, day-1, day_1, challenge 1, etc.
        patterns = [
            r'day[\s\-_]?(\d{1,2})',
            r'challenge[\s\-_]?(\d{1,2})',
            r'day[\s\-_]?0?([1-9]|[12][0-9]|30)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                day = int(match.group(1))
                if 1 <= day <= 30:
                    return day, 0.95
        
        return None, 0.0
    
    def _check_folder_path(self, paths: list) -> Tuple[Optional[int], float]:
        """Check folder paths for day indicators"""
        for path in paths:
            path_lower = path.lower()
            
            # Pattern: /day-1/, /day1/, /1/, etc.
            patterns = [
                r'/day[\-_]?(\d{1,2})/',
                r'/(\d{1,2})/'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, path_lower)
                if match:
                    day = int(match.group(1))
                    if 1 <= day <= 30:
                        return day, 0.90
        
        return None, 0.0
    
    def _match_contract_name_exact(self, file_names: list) -> Tuple[Optional[int], float]:
        """Exact match against challenge contract names"""
        for file_name in file_names:
            file_name_clean = file_name.replace('.sol', '')
            
            for day, challenge in self.challenges.items():
                expected_name = challenge['contractName'].replace('.sol', '')
                
                if file_name_clean.lower() == expected_name.lower():
                    return day, 0.95
        
        return None, 0.0
    
    def _check_filename_pattern(self, file_names: list) -> Tuple[Optional[int], float]:
        """Check file names for day patterns"""
        for file_name in file_names:
            file_name_lower = file_name.lower()
            
            # Pattern: day1.sol, day-1.sol, challenge1.sol, 1-counter.sol
            patterns = [
                r'day[\-_]?(\d{1,2})\.sol',
                r'challenge[\-_]?(\d{1,2})\.sol',
                r'^(\d{1,2})[\-_].*\.sol'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, file_name_lower)
                if match:
                    day = int(match.group(1))
                    if 1 <= day <= 30:
                        return day, 0.70
        
        return None, 0.0
    
    def _match_contract_name_fuzzy(self, file_names: list) -> Tuple[Optional[int], float]:
        """Fuzzy match against challenge contract names"""
        best_day = None
        best_score = 0.0
        
        for file_name in file_names:
            file_name_clean = file_name.replace('.sol', '').lower()
            
            for day, challenge in self.challenges.items():
                expected_name = challenge['contractName'].replace('.sol', '').lower()
                
                # Check if expected name is in file name
                if expected_name in file_name_clean:
                    score = 0.80
                    if score > best_score:
                        best_day = day
                        best_score = score
                
                # Check if file name is in expected name
                if file_name_clean in expected_name:
                    score = 0.75
                    if score > best_score:
                        best_day = day
                        best_score = score
                
                # Fuzzy string matching
                similarity = fuzz.ratio(file_name_clean, expected_name) / 100.0
                if similarity > 0.7 and similarity > best_score:
                    best_day = day
                    best_score = similarity * 0.85
        
        if best_day and best_score > 0.60:
            return best_day, best_score
        
        return None, 0.0
    
    def get_challenge_info(self, day: int) -> dict:
        """Get challenge information for a specific day"""
        return self.challenges.get(day, {})
