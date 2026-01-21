"""
Token Optimizer - Reduces token count by removing comments and whitespace
"""
import re


class TokenOptimizer:
    """Optimizes Solidity code to reduce token count for AI analysis"""
    
    @staticmethod
    def optimize(code: str) -> str:
        """
        Optimize Solidity code by removing comments and extra whitespace
        
        Args:
            code: Original Solidity source code
            
        Returns:
            Optimized code with minimal tokens
        """
        # Remove SPDX license identifiers
        code = re.sub(r'//\s*SPDX-License-Identifier:.*?\n', '', code)
        
        # Remove single-line comments
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        # Remove multi-line comments (including NatSpec)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Remove NatSpec comments
        code = re.sub(r'///.*?$', '', code, flags=re.MULTILINE)
        
        # Remove extra blank lines
        code = re.sub(r'\n\s*\n+', '\n', code)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in code.split('\n')]
        code = '\n'.join(lines)
        
        # Remove empty lines
        code = '\n'.join([line for line in code.split('\n') if line])
        
        return code.strip()
    
    @staticmethod
    def estimate_tokens(code: str) -> int:
        """
        Estimate token count (rough approximation)
        
        Args:
            code: Source code
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(code) // 4
    
    @staticmethod
    def get_savings(original: str, optimized: str) -> dict:
        """
        Calculate token savings
        
        Args:
            original: Original code
            optimized: Optimized code
            
        Returns:
            Dictionary with savings statistics
        """
        original_tokens = TokenOptimizer.estimate_tokens(original)
        optimized_tokens = TokenOptimizer.estimate_tokens(optimized)
        saved = original_tokens - optimized_tokens
        
        return {
            'original_tokens': original_tokens,
            'optimized_tokens': optimized_tokens,
            'tokens_saved': saved,
            'percentage_saved': (saved / original_tokens * 100) if original_tokens > 0 else 0
        }
