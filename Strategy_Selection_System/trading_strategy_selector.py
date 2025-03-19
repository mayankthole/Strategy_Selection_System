import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from datetime import datetime
import json
import pickle
from functools import partial
import seaborn as sns

class ExcelDataManager:
    def __init__(self, data_directory="strategy_data"):
        """Initialize with directory containing strategy Excel files"""
        self.data_directory = data_directory
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)
        self.strategy_files = {}
        self.strategy_data = {}
        
    def scan_for_strategy_files(self):
        """Scan directory for Excel files and identify strategies"""
        strategy_files = {}
        for filename in os.listdir(self.data_directory):
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                filepath = os.path.join(self.data_directory, filename)
                
                # Extract strategy name from filename
                strategy_name = filename.split('.')[0]
                if strategy_name not in strategy_files:
                    strategy_files[strategy_name] = []
                strategy_files[strategy_name].append(filepath)
                    
        self.strategy_files = strategy_files
        return strategy_files
    
    def get_available_strategies(self):
        """Return list of available strategies"""
        if not self.strategy_files:
            self.scan_for_strategy_files()
        return list(self.strategy_files.keys())
    
    def import_strategy_data(self, strategy_name):
        """Import data for a specific strategy"""
        if not self.strategy_files:
            self.scan_for_strategy_files()
            
        if strategy_name not in self.strategy_files:
            return None
            
        all_data = []
        for filepath in self.strategy_files[strategy_name]:
            try:
                # Read Excel data
                df = pd.read_excel(filepath)
                
                # Standardize column names
                df = self._standardize_columns(df)
                
                # Add strategy name column
                df['strategy_name'] = strategy_name
                
                # Add to combined data
                all_data.append(df)
            except Exception as e:
                print(f"Error importing {strategy_name} from {filepath}: {str(e)}")
                
        if all_data:
            # Combine all data sources for this strategy
            combined_data = pd.concat(all_data, ignore_index=True)
            # Remove duplicates by date
            if 'date' in combined_data.columns:
                combined_data = combined_data.drop_duplicates(subset=['date'])
                
            # Store in strategy_data dictionary
            self.strategy_data[strategy_name] = combined_data
            
            return combined_data
        
        return None
    
    def import_all_strategies(self):
        """Import data for all available strategies"""
        for strategy_name in self.get_available_strategies():
            self.import_strategy_data(strategy_name)
        return self.strategy_data
    
    def import_file(self, filepath):
        """Import a single Excel file"""
        try:
            # Extract strategy name from filename
            filename = os.path.basename(filepath)
            strategy_name = filename.split('.')[0]
            
            # Create strategy data directory if it doesn't exist
            if not os.path.exists(self.data_directory):
                os.makedirs(self.data_directory)
                
            # Copy file to strategy data directory
            import shutil
            destination = os.path.join(self.data_directory, filename)
            shutil.copy2(filepath, destination)
            
            # Update strategy files
            if strategy_name not in self.strategy_files:
                self.strategy_files[strategy_name] = []
            self.strategy_files[strategy_name].append(destination)
            
            # Import data
            df = pd.read_excel(filepath)
            df = self._standardize_columns(df)
            df['strategy_name'] = strategy_name
            
            # Store in strategy_data
            self.strategy_data[strategy_name] = df
            
            return strategy_name
        except Exception as e:
            print(f"Error importing file {filepath}: {str(e)}")
            return None
        
    def _standardize_columns(self, df):
        """Standardize column names to match our expected format"""
        # First, try to identify the required columns
        prev_vix_high_col = None
        prev_vix_low_col = None
        prev_index_high_col = None
        prev_index_low_col = None
        pnl_col = None
        date_col = None
        
        # Print available columns for debugging
        print("Available columns in Excel file:", df.columns.tolist())
        
        # Look for specific columns
        for col in df.columns:
            col_lower = col.lower()
            if 'date' in col_lower:
                date_col = col
            elif 'final mtm' in col_lower:
                pnl_col = col
            elif 'previous day vix high' in col_lower:
                prev_vix_high_col = col
            elif 'previous day vix low' in col_lower:
                prev_vix_low_col = col
            elif 'previous day index high' in col_lower:
                prev_index_high_col = col
            elif 'previous day index low' in col_lower:
                prev_index_low_col = col
        
        # If columns aren't found, look for alternative naming patterns
        if not prev_vix_high_col:
            for col in df.columns:
                col_lower = col.lower()
                if 'vix' in col_lower and 'high' in col_lower and ('prev' in col_lower or 'previous' in col_lower):
                    prev_vix_high_col = col
                    break
        
        if not prev_vix_low_col:
            for col in df.columns:
                col_lower = col.lower()
                if 'vix' in col_lower and 'low' in col_lower and ('prev' in col_lower or 'previous' in col_lower):
                    prev_vix_low_col = col
                    break
        
        if not prev_index_high_col:
            for col in df.columns:
                col_lower = col.lower()
                if ('index' in col_lower or 'nifty' in col_lower) and 'high' in col_lower and ('prev' in col_lower or 'previous' in col_lower):
                    prev_index_high_col = col
                    break
        
        if not prev_index_low_col:
            for col in df.columns:
                col_lower = col.lower()
                if ('index' in col_lower or 'nifty' in col_lower) and 'low' in col_lower and ('prev' in col_lower or 'previous' in col_lower):
                    prev_index_low_col = col
                    break
        
        if not pnl_col:
            for col in df.columns:
                col_lower = col.lower()
                if 'final' in col_lower and 'mtm' in col_lower:
                    pnl_col = col
                    break
                elif 'pnl' in col_lower or 'p&l' in col_lower or 'profit' in col_lower:
                    pnl_col = col
                    break
        
        # Create the new column mappings
        new_columns = {}
        if date_col:
            new_columns[date_col] = 'date'
        if prev_vix_high_col:
            new_columns[prev_vix_high_col] = 'prev_vix_high'
        if prev_vix_low_col:
            new_columns[prev_vix_low_col] = 'prev_vix_low'
        if prev_index_high_col:
            new_columns[prev_index_high_col] = 'prev_index_high'
        if prev_index_low_col:
            new_columns[prev_index_low_col] = 'prev_index_low'
        if pnl_col:
            new_columns[pnl_col] = 'pnl'
        
        # Print identified columns
        print("Columns identified for standardization:", new_columns)
        
        # Rename columns
        return df.rename(columns=new_columns)

class StrategyAnalyzer:






    def calculate_sqn(self, trades_data):
        """
        Calculate System Quality Number (SQN) for a set of trades
        
        Parameters:
        trades_data: DataFrame containing trade results with 'pnl' column
        
        Returns:
        sqn: System Quality Number
        """
        if len(trades_data) < 5:  # Need minimum sample size
            return None
            
        avg_profit = trades_data['pnl'].mean()
        std_dev = trades_data['pnl'].std()
        num_trades = len(trades_data)
        
        # Avoid division by zero
        if std_dev == 0 or np.isnan(std_dev):
            return None
            
        sqn = (avg_profit / std_dev) * np.sqrt(num_trades)
        return sqn











    def __init__(self, data_manager):
        """Initialize with a data manager"""
        self.data_manager = data_manager
        self.strategy_metrics = {}
        self.vix_range_performance = {}
        self.monthly_performance = {}
        self.vix_range_sqn = {}
        self.monthly_sqn = {}
        
    def analyze_all_strategies(self):
        """Analyze performance metrics for all strategies"""
        for strategy_name, data in self.data_manager.strategy_data.items():
            self.analyze_strategy(strategy_name, data)
        return self.strategy_metrics
    
    def analyze_strategy(self, strategy_name, data=None):
        """Analyze performance metrics for a single strategy"""
        if data is None:
            data = self.data_manager.strategy_data.get(strategy_name)
            if data is None:
                return None
                
        # Ensure we have the required columns
        required_columns = ['date', 'pnl', 'prev_vix_high', 'prev_vix_low', 
                            'prev_index_high', 'prev_index_low']
        
        # Check if all required columns exist
        for col in required_columns:
            if col not in data.columns:
                # If a required column is missing, try to find an equivalent
                if col == 'pnl' and any(c for c in data.columns if 'mtm' in c.lower()):
                    # Use Final MTM as pnl
                    mtm_col = next(c for c in data.columns if 'final mtm' in c.lower())
                    data['pnl'] = data[mtm_col]
                elif 'vix' in col and 'high' in col:
                    vix_high_col = next((c for c in data.columns if 'vix' in c.lower() and 'high' in c.lower() and 'prev' in c.lower()), None)
                    if vix_high_col:
                        data['prev_vix_high'] = data[vix_high_col]
                elif 'vix' in col and 'low' in col:
                    vix_low_col = next((c for c in data.columns if 'vix' in c.lower() and 'low' in c.lower() and 'prev' in c.lower()), None)
                    if vix_low_col:
                        data['prev_vix_low'] = data[vix_low_col]
                elif 'index' in col and 'high' in col:
                    idx_high_col = next((c for c in data.columns if 'index' in c.lower() and 'high' in c.lower() and 'prev' in c.lower()), None)
                    if idx_high_col:
                        data['prev_index_high'] = data[idx_high_col]
                elif 'index' in col and 'low' in col:
                    idx_low_col = next((c for c in data.columns if 'index' in c.lower() and 'low' in c.lower() and 'prev' in c.lower()), None)
                    if idx_low_col:
                        data['prev_index_low'] = data[idx_low_col]
                else:
                    print(f"Missing required column: {col}")
                    return None
        
        # Calculate derived metrics
        data['prev_vix_range'] = data['prev_vix_high'] - data['prev_vix_low']
        data['prev_index_range'] = data['prev_index_high'] - data['prev_index_low']
        
        # Convert date column to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(data['date']):
            data['date'] = pd.to_datetime(data['date'])
        
        # Add month column
        data['month'] = data['date'].dt.month
        
        # Calculate profitability metrics
        profitable_days = data[data['pnl'] > 0]
        unprofitable_days = data[data['pnl'] <= 0]
        
        win_rate = len(profitable_days) / len(data) if len(data) > 0 else 0
        avg_profit = profitable_days['pnl'].mean() if len(profitable_days) > 0 else 0
        avg_loss = unprofitable_days['pnl'].mean() if len(unprofitable_days) > 0 else 0
        profit_factor = abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')
        
        # Calculate correlations
        correlations = {}
        for feature in ['prev_vix_range', 'prev_index_range']:
            correlations[feature] = data[feature].corr(data['pnl'])
        
        # Analyze performance by VIX range
        vix_bins = [
            {'name': 'Very Low', 'min': 0, 'max': 1},
            {'name': 'Low', 'min': 1, 'max': 1.5},
            {'name': 'Medium', 'min': 1.5, 'max': 2},
            {'name': 'High', 'min': 2, 'max': 3},
            {'name': 'Very High', 'min': 3, 'max': float('inf')}
        ]
        
        # Create a dictionary to map bin names to ranges for SQN calculation
        vix_bins_dict = {bin['name']: bin for bin in vix_bins}
        
        vix_performance = {}
        vix_range_sqn = {}  # New dictionary for SQN by VIX range
        
        for bin in vix_bins:
            bin_data = data[(data['prev_vix_range'] >= bin['min']) & (data['prev_vix_range'] < bin['max'])]
            if len(bin_data) > 0:
                bin_win_rate = len(bin_data[bin_data['pnl'] > 0]) / len(bin_data)
                bin_avg_pnl = bin_data['pnl'].mean()
                vix_performance[bin['name']] = {
                    'count': len(bin_data),
                    'win_rate': bin_win_rate,
                    'avg_pnl': bin_avg_pnl
                }
                
                # Calculate SQN if we have enough data points
                if len(bin_data) >= 5:  # Minimum sample size for statistical significance
                    avg_profit = bin_data['pnl'].mean()
                    std_dev = bin_data['pnl'].std()
                    num_trades = len(bin_data)
                    
                    # Avoid division by zero
                    if std_dev > 0 and not np.isnan(std_dev):
                        sqn = (avg_profit / std_dev) * np.sqrt(num_trades)
                        vix_range_sqn[bin['name']] = sqn
        
        # Analyze monthly performance
        monthly_perf = {}
        monthly_sqn = {}  # New dictionary for SQN by month
        
        for month in range(1, 13):
            month_data = data[data['month'] == month]
            if len(month_data) > 0:
                month_win_rate = len(month_data[month_data['pnl'] > 0]) / len(month_data)
                month_avg_pnl = month_data['pnl'].mean()
                monthly_perf[month] = {
                    'count': len(month_data),
                    'win_rate': month_win_rate,
                    'avg_pnl': month_avg_pnl
                }
                
                # Calculate SQN if we have enough data points
                if len(month_data) >= 5:  # Minimum sample size
                    avg_profit = month_data['pnl'].mean()
                    std_dev = month_data['pnl'].std()
                    num_trades = len(month_data)
                    
                    # Avoid division by zero
                    if std_dev > 0 and not np.isnan(std_dev):
                        sqn = (avg_profit / std_dev) * np.sqrt(num_trades)
                        monthly_sqn[month] = sqn
        
        # Calculate overall SQN
        overall_sqn = None
        if len(data) >= 5:
            avg_profit = data['pnl'].mean()
            std_dev = data['pnl'].std()
            num_trades = len(data)
            
            if std_dev > 0 and not np.isnan(std_dev):
                overall_sqn = (avg_profit / std_dev) * np.sqrt(num_trades)
        
        # Store metrics
        self.strategy_metrics[strategy_name] = {
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': data['pnl'].sum(),
            'correlations': correlations,
            'overall_sqn': overall_sqn  # Add overall SQN to metrics
        }
        
        self.vix_range_performance[strategy_name] = vix_performance
        self.monthly_performance[strategy_name] = monthly_perf
        
        # Store SQN metrics
        if not hasattr(self, 'vix_range_sqn'):
            self.vix_range_sqn = {}
        if not hasattr(self, 'monthly_sqn'):
            self.monthly_sqn = {}
            
        self.vix_range_sqn[strategy_name] = vix_range_sqn
        self.monthly_sqn[strategy_name] = monthly_sqn
        
        return self.strategy_metrics[strategy_name]
    
    def predict_performance(self, prev_vix_high, prev_vix_low, prev_index_high, prev_index_low, trade_date=None):
        """Predict performance for all strategies based on market conditions"""
        if trade_date is None:
            trade_date = datetime.now()
        elif isinstance(trade_date, str):
            trade_date = datetime.strptime(trade_date, '%Y-%m-%d')
            
        # Calculate ranges
        prev_vix_range = prev_vix_high - prev_vix_low
        prev_index_range = prev_index_high - prev_index_low
        
        # Get month
        month = trade_date.month
        
        # Determine VIX range category
        vix_category = 'Medium'  # Default
        if prev_vix_range < 1:
            vix_category = 'Very Low'
        elif prev_vix_range < 1.5:
            vix_category = 'Low'
        elif prev_vix_range < 2:
            vix_category = 'Medium'
        elif prev_vix_range < 3:
            vix_category = 'High'
        else:
            vix_category = 'Very High'
            
        # Predict performance for each strategy
        predictions = {}
        for strategy_name in self.strategy_metrics.keys():
            # Get VIX range performance
            vix_perf = self.vix_range_performance.get(strategy_name, {}).get(vix_category, {})
            vix_win_rate = vix_perf.get('win_rate', 0.5)
            vix_avg_pnl = vix_perf.get('avg_pnl', 0)
            
            # Get monthly performance
            month_perf = self.monthly_performance.get(strategy_name, {}).get(month, {})
            month_win_rate = month_perf.get('win_rate', 0.5)
            month_avg_pnl = month_perf.get('avg_pnl', 0)
            
            # Get correlation impact
            correlations = self.strategy_metrics[strategy_name]['correlations']
            vix_corr = correlations.get('prev_vix_range', 0)
            index_corr = correlations.get('prev_index_range', 0)
            
            # Calculate expected P&L
            # Blend VIX and month-based P&L predictions
            expected_pnl = (vix_avg_pnl * 0.6) + (month_avg_pnl * 0.4)
            
            # Adjust based on correlations
            # If VIX range has positive correlation and current VIX range is high, increase expected P&L
            vix_adjustment = vix_corr * (prev_vix_range - 1.5) * 5000
            # If index range has negative correlation and current index range is high, decrease expected P&L
            index_adjustment = index_corr * (prev_index_range - 150) * 50
            
            expected_pnl += vix_adjustment + index_adjustment
            
            # Calculate win probability
            win_prob = (vix_win_rate * 0.6) + (month_win_rate * 0.4)
            win_prob = max(0.3, min(0.9, win_prob))  # Cap between 30% and 90%
            
            # Calculate confidence score (0-100)
            # Higher scores = more confidence in prediction
            vix_conf = 50 + ((vix_perf.get('count', 0) / 10) * 10)  # More data = more confidence
            month_conf = 50 + ((month_perf.get('count', 0) / 5) * 10)
            confidence = (vix_conf * 0.6) + (month_conf * 0.4)
            confidence = min(confidence, 100)
            
            # Calculate decision score (similar to our excel approach)
            vix_score = min(prev_vix_range * 30, 60)
            index_score = min(max(20 - (prev_index_range / 20), 0), 20)
            
            # Month score based on performance
            month_factor = self.monthly_performance.get(strategy_name, {}).get(month, {}).get('win_rate', 0.5)
            month_score = (month_factor - 0.5) * 40  # Scale to -20 to +20
            
            # Get SQN values for the current conditions
            vix_sqn = None
            month_sqn = None
            
            if hasattr(self, 'vix_range_sqn'):
                vix_sqn = self.vix_range_sqn.get(strategy_name, {}).get(vix_category)
                
            if hasattr(self, 'monthly_sqn'):
                month_sqn = self.monthly_sqn.get(strategy_name, {}).get(month)
            
            # Calculate SQN adjustment (0-15 points)
            sqn_adjustment = 0
            if vix_sqn is not None:
                if vix_sqn >= 4.0:
                    sqn_adjustment += 15  # Excellent SQN
                elif vix_sqn >= 3.0:
                    sqn_adjustment += 10  # Good SQN
                elif vix_sqn >= 2.0:
                    sqn_adjustment += 5   # Average SQN
                # Poor SQN gets no adjustment
            
            # Add SQN adjustment to decision score
            decision_score = vix_score + index_score + month_score + sqn_adjustment
            
            # Determine recommendation
            if decision_score >= 70:
                recommendation = "HIGHLY RECOMMENDED"
                position_size = "100%"
            elif decision_score >= 60:
                recommendation = "RECOMMENDED"
                position_size = "75%"
            elif decision_score >= 50:
                recommendation = "NEUTRAL"
                position_size = "50%"
            else:
                recommendation = "NOT RECOMMENDED"
                position_size = "0%"
            
            # Get overall SQN if available
            overall_sqn = self.strategy_metrics[strategy_name].get('overall_sqn')
            
            # Create SQN rating
            sqn_rating = None
            if vix_sqn is not None:
                if vix_sqn < 1.0:
                    sqn_rating = "Poor"
                elif vix_sqn < 2.0:
                    sqn_rating = "Below Average"
                elif vix_sqn < 3.0:
                    sqn_rating = "Average"
                elif vix_sqn < 5.0:
                    sqn_rating = "Good"
                elif vix_sqn < 7.0:
                    sqn_rating = "Excellent"
                else:
                    sqn_rating = "Superb"
            
            predictions[strategy_name] = {
                'expected_pnl': expected_pnl,
                'win_probability': win_prob * 100,
                'confidence': confidence,
                'decision_score': decision_score,
                'recommendation': recommendation,
                'position_size': position_size,
                'vix_category': vix_category,
                'vix_performance': vix_perf,
                'month_performance': month_perf,
                'sqn_values': {
                    'overall_sqn': overall_sqn,
                    'vix_sqn': vix_sqn,
                    'month_sqn': month_sqn,
                    'sqn_rating': sqn_rating
                },
                'sqn_adjustment': sqn_adjustment
            }
            
        # Rank strategies by expected P&L
        ranked_strategies = sorted(predictions.items(), key=lambda x: x[1]['expected_pnl'], reverse=True)
        
        return {
            'predictions': predictions,
            'ranked_strategies': ranked_strategies,
            'market_conditions': {
                'prev_vix_high': prev_vix_high,
                'prev_vix_low': prev_vix_low,
                'prev_index_high': prev_index_high,
                'prev_index_low': prev_index_low,
                'prev_vix_range': prev_vix_range,
                'prev_index_range': prev_index_range,
                'vix_category': vix_category,
                'month': month,
                'date': trade_date.strftime('%Y-%m-%d')
            }
        }

class StrategySelectionApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Trading Strategy Selection Platform")
        self.root.geometry("1200x800")
        
        # Set up the data manager and analyzer
        self.data_manager = ExcelDataManager()
        self.analyzer = StrategyAnalyzer(self.data_manager)
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        self.tab1 = ttk.Frame(self.tab_control)  # Strategy Selection
        self.tab2 = ttk.Frame(self.tab_control)  # Strategy Data Management
        self.tab3 = ttk.Frame(self.tab_control)  # Performance Analytics
        self.tab4 = ttk.Frame(self.tab_control)  # Settings
        
        self.tab_control.add(self.tab1, text='Strategy Selection')
        self.tab_control.add(self.tab2, text='Data Management')
        self.tab_control.add(self.tab3, text='Analytics')
        self.tab_control.add(self.tab4, text='Settings')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Initialize tabs
        self.setup_selection_tab()
        self.setup_data_tab()
        self.setup_analytics_tab()
        self.setup_settings_tab()
        
        # Load any existing data
        self.load_data()







    def generate_sqn_analytics(self, strategy_name):
        """Generate SQN analytics visualization"""
        # Get SQN data
        vix_sqn = self.analyzer.vix_range_sqn.get(strategy_name, {})
        monthly_sqn = self.analyzer.monthly_sqn.get(strategy_name, {})
        
        # Clear figure
        self.sqn_fig.clear()
        
        # Create subplots
        gs = self.sqn_fig.add_gridspec(2, 1)
        ax1 = self.sqn_fig.add_subplot(gs[0, 0])
        ax2 = self.sqn_fig.add_subplot(gs[1, 0])
        
        # Plot VIX range SQN
        categories = []
        sqn_values = []
        for category in ['Very Low', 'Low', 'Medium', 'High', 'Very High']:
            if category in vix_sqn and vix_sqn[category] is not None:
                categories.append(category)
                sqn_values.append(vix_sqn[category])
        
        if categories:
            bars = ax1.bar(categories, sqn_values)
            ax1.set_title('System Quality Number (SQN) by VIX Category')
            ax1.set_ylabel('SQN Value')
            
            # Color code bars
            for bar, sqn in zip(bars, sqn_values):
                if sqn < 1.0:
                    bar.set_color('red')
                elif sqn < 2.0:
                    bar.set_color('orange')
                elif sqn < 3.0:
                    bar.set_color('yellow')
                elif sqn < 5.0:
                    bar.set_color('lightgreen')
                else:
                    bar.set_color('green')
                    
            # Add reference lines
            ax1.axhline(y=1.0, color='r', linestyle='--', alpha=0.3)
            ax1.axhline(y=2.0, color='orange', linestyle='--', alpha=0.3)
            ax1.axhline(y=3.0, color='green', linestyle='--', alpha=0.3)
        
        # Plot monthly SQN
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        months = []
        sqn_values = []
        
        for month in range(1, 13):
            if month in monthly_sqn and monthly_sqn[month] is not None:
                months.append(month_names[month-1])
                sqn_values.append(monthly_sqn[month])
        
        if months:
            bars = ax2.bar(months, sqn_values)
            ax2.set_title('System Quality Number (SQN) by Month')
            ax2.set_ylabel('SQN Value')
            
            # Color code bars
            for bar, sqn in zip(bars, sqn_values):
                if sqn < 1.0:
                    bar.set_color('red')
                elif sqn < 2.0:
                    bar.set_color('orange')
                elif sqn < 3.0:
                    bar.set_color('yellow')
                elif sqn < 5.0:
                    bar.set_color('lightgreen')
                else:
                    bar.set_color('green')
                    
            # Add reference lines
            ax2.axhline(y=1.0, color='r', linestyle='--', alpha=0.3)
            ax2.axhline(y=2.0, color='orange', linestyle='--', alpha=0.3)
            ax2.axhline(y=3.0, color='green', linestyle='--', alpha=0.3)
        
        # Add title and SQN rating guide
        self.sqn_fig.suptitle(f"SQN Analysis: {strategy_name}", fontsize=14)
        
        # Add SQN rating guide text at the bottom
        rating_text = "SQN Rating Scale: <1.0: Poor | 1.0-1.9: Below Average | 2.0-2.9: Average | 3.0-4.9: Good | 5.0-6.9: Excellent | 7.0+: Superb"
        self.sqn_fig.text(0.5, 0.01, rating_text, ha='center', fontsize=9)
        
        # Adjust layout
        self.sqn_fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Draw canvas
        self.sqn_canvas.draw()    
        





    def setup_selection_tab(self):
        # Input frame
        input_frame = ttk.LabelFrame(self.tab1, text="Market Conditions")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Input fields
        ttk.Label(input_frame, text="Previous Day VIX High:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.vix_high_entry = ttk.Entry(input_frame)
        self.vix_high_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Previous Day VIX Low:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.vix_low_entry = ttk.Entry(input_frame)
        self.vix_low_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Previous Day Index High:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.index_high_entry = ttk.Entry(input_frame)
        self.index_high_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Previous Day Index Low:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.index_low_entry = ttk.Entry(input_frame)
        self.index_low_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Trade Date (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = ttk.Entry(input_frame)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_entry.grid(row=4, column=1, padx=5, pady=5)
        
        # Calculate button
        calculate_button = ttk.Button(input_frame, text="Find Best Strategies", command=self.calculate_strategies)
        calculate_button.grid(row=5, column=0, columnspan=2, padx=5, pady=10)
        
        # Results frame
        self.results_frame = ttk.LabelFrame(self.tab1, text="Strategy Recommendations")
        self.results_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        # Create a frame for the treeview
        tree_frame = ttk.Frame(self.results_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar to the treeview
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Strategy results treeview
        self.results_tree = ttk.Treeview(tree_frame, columns=("rank", "strategy", "expected_pnl", "win_prob", "recommendation"), 
                                         show="headings", height=10, yscrollcommand=scrollbar.set)
        self.results_tree.pack(fill="both", expand=True)
        
        scrollbar.config(command=self.results_tree.yview)
        
        # Define columns
        self.results_tree.column("rank", width=50, anchor="center")
        self.results_tree.column("strategy", width=150, anchor="w")
        self.results_tree.column("expected_pnl", width=100, anchor="e")
        self.results_tree.column("win_prob", width=100, anchor="center")
        self.results_tree.column("recommendation", width=150, anchor="center")
        
        # Define headings
        self.results_tree.heading("rank", text="Rank")
        self.results_tree.heading("strategy", text="Strategy")
        self.results_tree.heading("expected_pnl", text="Expected P&L")
        self.results_tree.heading("win_prob", text="Win Probability")
        self.results_tree.heading("recommendation", text="Recommendation")
        
        # Strategy details frame
        self.details_frame = ttk.LabelFrame(self.tab1, text="Strategy Details")
        self.details_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Add a label to display details
        self.details_text = tk.Text(self.details_frame, wrap="word", width=40, height=15)
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Bind treeview selection to show details
        self.results_tree.bind("<<TreeviewSelect>>", self.show_strategy_details)
        
        # Configure grid weights
        self.tab1.columnconfigure(1, weight=1)
        self.tab1.rowconfigure(1, weight=1)
        
    def setup_data_tab(self):
        # Data management frame
        data_frame = ttk.LabelFrame(self.tab2, text="Strategy Data Management")
        data_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Strategy list frame
        list_frame = ttk.Frame(data_frame)
        list_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(list_frame, text="Available Strategies:").pack(anchor="w", padx=5, pady=5)
        
        # Create a frame for the treeview
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar to the treeview
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Strategy list treeview
        self.strategy_tree = ttk.Treeview(tree_frame, columns=("strategy", "trades", "win_rate", "pnl"), 
                                         show="headings", height=15, yscrollcommand=scrollbar.set)
        self.strategy_tree.pack(fill="both", expand=True)
        
        scrollbar.config(command=self.strategy_tree.yview)
        
        # Define columns
        self.strategy_tree.column("strategy", width=150, anchor="w")
        self.strategy_tree.column("trades", width=70, anchor="center")
        self.strategy_tree.column("win_rate", width=100, anchor="center")
        self.strategy_tree.column("pnl", width=100, anchor="e")
        
        # Define headings
        self.strategy_tree.heading("strategy", text="Strategy")
        self.strategy_tree.heading("trades", text="# Trades")
        self.strategy_tree.heading("win_rate", text="Win Rate")
        self.strategy_tree.heading("pnl", text="Total P&L")
        
        # Button frame
        button_frame = ttk.Frame(data_frame)
        button_frame.pack(side="right", fill="y", padx=5, pady=5)
        
        # Buttons for data management
        ttk.Button(button_frame, text="Import Excel File", command=self.import_excel_file).pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="Refresh Strategy List", command=self.refresh_strategies).pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="View Strategy Data", command=self.view_strategy_data).pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="Remove Strategy", command=self.remove_strategy).pack(fill="x", padx=5, pady=5)
        
    def setup_analytics_tab(self):
            # Create a frame for the analytics
            analytics_frame = ttk.Frame(self.tab3)
            analytics_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create a frame for the strategy selection
            select_frame = ttk.Frame(analytics_frame)
            select_frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(select_frame, text="Select Strategy:").pack(side="left", padx=5, pady=5)
            self.analytics_strategy_var = tk.StringVar()
            self.analytics_strategy_combo = ttk.Combobox(select_frame, textvariable=self.analytics_strategy_var)
            self.analytics_strategy_combo.pack(side="left", padx=5, pady=5)
            
            ttk.Button(select_frame, text="Analyze", command=self.analyze_strategy).pack(side="left", padx=5, pady=5)
            
            # Create a notebook for different analytics views
            self.analytics_notebook = ttk.Notebook(analytics_frame)
            self.analytics_notebook.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Create tabs for different analytics
            self.overview_tab = ttk.Frame(self.analytics_notebook)
            self.vix_tab = ttk.Frame(self.analytics_notebook)
            self.monthly_tab = ttk.Frame(self.analytics_notebook)
            self.corr_tab = ttk.Frame(self.analytics_notebook)
            self.sqn_tab = ttk.Frame(self.analytics_notebook)  # Add SQN tab
            
            self.analytics_notebook.add(self.overview_tab, text="Overview")
            self.analytics_notebook.add(self.vix_tab, text="VIX Analysis")
            self.analytics_notebook.add(self.monthly_tab, text="Monthly Analysis")
            self.analytics_notebook.add(self.corr_tab, text="Correlations")
            self.analytics_notebook.add(self.sqn_tab, text="SQN Analysis")  # Add SQN tab
            
            # Initialize figures for each tab
            self.setup_analytics_figures()


    def setup_analytics_figures(self):

            # Overview tab
            self.overview_fig = plt.Figure(figsize=(10, 6))
            self.overview_canvas = FigureCanvasTkAgg(self.overview_fig, self.overview_tab)
            self.overview_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # VIX Analysis tab
            self.vix_fig = plt.Figure(figsize=(10, 6))
            self.vix_canvas = FigureCanvasTkAgg(self.vix_fig, self.vix_tab)
            self.vix_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Monthly Analysis tab
            self.monthly_fig = plt.Figure(figsize=(10, 6))
            self.monthly_canvas = FigureCanvasTkAgg(self.monthly_fig, self.monthly_tab)
            self.monthly_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # Correlations tab
            self.corr_fig = plt.Figure(figsize=(10, 6))
            self.corr_canvas = FigureCanvasTkAgg(self.corr_fig, self.corr_tab)
            self.corr_canvas.get_tk_widget().pack(fill="both", expand=True)
            
            # SQN Analysis tab
            self.sqn_fig = plt.Figure(figsize=(10, 6))
            self.sqn_canvas = FigureCanvasTkAgg(self.sqn_fig, self.sqn_tab)
            self.sqn_canvas.get_tk_widget().pack(fill="both", expand=True)



    def setup_settings_tab(self):
        # Settings frame
        settings_frame = ttk.LabelFrame(self.tab4, text="Application Settings")
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Data directory
        ttk.Label(settings_frame, text="Data Directory:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.data_dir_entry = ttk.Entry(settings_frame, width=40)
        self.data_dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.data_dir_entry.insert(0, self.data_manager.data_directory)
        
        ttk.Button(settings_frame, text="Browse", command=self.browse_data_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # Save settings button
        ttk.Button(settings_frame, text="Save Settings", command=self.save_settings).grid(row=1, column=1, padx=5, pady=10)
        
        # App information
        info_frame = ttk.LabelFrame(self.tab4, text="About")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        info_text = """
        Trading Strategy Selection Platform
        
        This application helps you select the best trading strategy
        based on current market conditions and historical performance.
        
        Instructions:
        1. Import your strategy data from Excel files
        2. Enter the current market conditions
        3. Get recommendations on which strategies to use
        
        Developed with ♥
        """
        
        info_label = ttk.Label(info_frame, text=info_text, justify="left")
        info_label.pack(padx=10, pady=10)

    def load_data(self):
        """Load existing strategy data"""
        try:
            # Check if the data directory exists
            if not os.path.exists(self.data_manager.data_directory):
                os.makedirs(self.data_manager.data_directory)
                return
            
            # Scan for strategy files
            self.data_manager.scan_for_strategy_files()
            
            # Import all strategies
            self.data_manager.import_all_strategies()
            
            # Analyze all strategies
            self.analyzer.analyze_all_strategies()
            
            # Update strategy list
            self.refresh_strategies()
            
            # Update analytics strategy combo
            self.update_analytics_combo()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def calculate_strategies(self):
        """Calculate and display strategy recommendations"""
        try:
            # Get values from input fields
            vix_high = float(self.vix_high_entry.get())
            vix_low = float(self.vix_low_entry.get())
            index_high = float(self.index_high_entry.get())
            index_low = float(self.index_low_entry.get())
            trade_date = self.date_entry.get()
            
            # Validate inputs
            if vix_high <= vix_low:
                messagebox.showerror("Input Error", "VIX High must be greater than VIX Low")
                return
                
            if index_high <= index_low:
                messagebox.showerror("Input Error", "Index High must be greater than Index Low")
                return
            
            # Check if we have any strategies to analyze
            if not self.analyzer.strategy_metrics:
                messagebox.showinfo("No Data", "No strategy data available. Please import strategy data first.")
                return
            
            # Get predictions
            result = self.analyzer.predict_performance(
                vix_high, vix_low, index_high, index_low, trade_date
            )
            
            # Clear the treeview
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            # Add ranked strategies to the treeview
            for i, (strategy, prediction) in enumerate(result['ranked_strategies']):
                rank = i + 1
                expected_pnl = f"₹{prediction['expected_pnl']:.2f}"
                win_prob = f"{prediction['win_probability']:.1f}%"
                
                # Add to treeview
                item_id = self.results_tree.insert("", "end", values=(rank, strategy, expected_pnl, win_prob, prediction['recommendation']))
                
                # Color code rows based on recommendation
                if prediction['recommendation'] == "HIGHLY RECOMMENDED":
                    self.results_tree.item(item_id, tags=("highly_recommended",))
                elif prediction['recommendation'] == "RECOMMENDED":
                    self.results_tree.item(item_id, tags=("recommended",))
                elif prediction['recommendation'] == "NEUTRAL":
                    self.results_tree.item(item_id, tags=("neutral",))
                else:
                    self.results_tree.item(item_id, tags=("not_recommended",))
            
            # Configure tag colors
            self.results_tree.tag_configure("highly_recommended", background="#a8e6cf")  # Light green
            self.results_tree.tag_configure("recommended", background="#dcedc1")  # Light yellow-green
            self.results_tree.tag_configure("neutral", background="#ffd3b6")  # Light orange
            self.results_tree.tag_configure("not_recommended", background="#ffaaa5")  # Light red
            
            # Store the predictions for later use
            self.current_predictions = result
            
            # Show details for the top strategy
            if result['ranked_strategies']:
                self.results_tree.selection_set(self.results_tree.get_children()[0])
                self.show_strategy_details(None)
            
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_strategy_details(self, event):
        """Show details for the selected strategy"""
        selected_items = self.results_tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.results_tree.item(item, "values")
        strategy_name = values[1]
        
        # Get prediction details for this strategy
        if not hasattr(self, 'current_predictions'):
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, "No prediction data available")
            return
            
        pred = self.current_predictions['predictions'].get(strategy_name)
        if not pred:
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, "No details available for this strategy")
            return
        
        # Display details
        self.details_text.delete(1.0, tk.END)
        
        # Market conditions
        market = self.current_predictions['market_conditions']
        self.details_text.insert(tk.END, f"Market Conditions:\n", "heading")
        self.details_text.insert(tk.END, f"Date: {market['date']}\n")
        self.details_text.insert(tk.END, f"Previous Day VIX Range: {market['prev_vix_range']:.2f} ({market['vix_category']})\n")
        self.details_text.insert(tk.END, f"Previous Day Index Range: {market['prev_index_range']:.2f}\n\n")
        
        # Strategy details
        self.details_text.insert(tk.END, f"Strategy: {strategy_name}\n", "heading")
        self.details_text.insert(tk.END, f"Expected P&L: ₹{pred['expected_pnl']:.2f}\n")
        self.details_text.insert(tk.END, f"Win Probability: {pred['win_probability']:.1f}%\n")
        self.details_text.insert(tk.END, f"Confidence: {pred['confidence']:.1f}%\n")
        self.details_text.insert(tk.END, f"Decision Score: {pred['decision_score']:.1f}\n")
        
        # Add SQN details if available
        if 'sqn_values' in pred:
            sqn_values = pred['sqn_values']
            vix_sqn = sqn_values.get('vix_sqn')
            sqn_rating = sqn_values.get('sqn_rating')
            
            if vix_sqn is not None:
                self.details_text.insert(tk.END, f"SQN in {market['vix_category']} VIX: {vix_sqn:.2f}")
                if sqn_adjustment := pred.get('sqn_adjustment', 0):
                    self.details_text.insert(tk.END, f" (+{sqn_adjustment} points)\n")
                else:
                    self.details_text.insert(tk.END, "\n")
                    
                if sqn_rating:
                    self.details_text.insert(tk.END, f"System Quality Rating: {sqn_rating}\n")
        
        self.details_text.insert(tk.END, f"Recommendation: {pred['recommendation']}\n")
        self.details_text.insert(tk.END, f"Position Size: {pred['position_size']}\n\n")
        
        # Historical performance in similar conditions
        self.details_text.insert(tk.END, "Historical Performance:\n", "heading")
        vix_perf = pred['vix_performance']
        if vix_perf:
            self.details_text.insert(tk.END, f"In {market['vix_category']} VIX ranges ({vix_perf.get('count', 0)} days):\n")
            self.details_text.insert(tk.END, f"  Win Rate: {vix_perf.get('win_rate', 0) * 100:.1f}%\n")
            self.details_text.insert(tk.END, f"  Avg P&L: ₹{vix_perf.get('avg_pnl', 0):.2f}\n\n")
        
        month_perf = pred['month_performance']
        month_name = datetime.strptime(str(market['month']), "%m").strftime("%B")
        if month_perf:
            self.details_text.insert(tk.END, f"In {month_name} ({month_perf.get('count', 0)} days):\n")
            self.details_text.insert(tk.END, f"  Win Rate: {month_perf.get('win_rate', 0) * 100:.1f}%\n")
            self.details_text.insert(tk.END, f"  Avg P&L: ₹{month_perf.get('avg_pnl', 0):.2f}\n")
        
        # Add SQN section if any SQN data is available
        if 'sqn_values' in pred:
            sqn_values = pred['sqn_values']
            overall_sqn = sqn_values.get('overall_sqn')
            month_sqn = sqn_values.get('month_sqn')
            
            if overall_sqn is not None or month_sqn is not None:
                self.details_text.insert(tk.END, "\nSystem Quality Numbers (SQN):\n", "heading")
                
                if overall_sqn is not None:
                    self.details_text.insert(tk.END, f"Overall Strategy SQN: {overall_sqn:.2f}\n")
                    
                if month_sqn is not None:
                    self.details_text.insert(tk.END, f"SQN in {month_name}: {month_sqn:.2f}\n")
                    
                # Add SQN interpretation guide
                self.details_text.insert(tk.END, "\nSQN Rating Scale:\n")
                self.details_text.insert(tk.END, "< 1.0: Poor | 1.0-1.9: Below Average | 2.0-2.9: Average\n")
                self.details_text.insert(tk.END, "3.0-4.9: Good | 5.0-6.9: Excellent | 7.0+: Superb\n")
        
        # Configure tags
        self.details_text.tag_configure("heading", font=("TkDefaultFont", 10, "bold"))



    def import_excel_file(self):
        """Import a strategy Excel file"""
        filepath = filedialog.askopenfilename(
            title="Select Strategy Excel File",
            filetypes=(("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
        )
        
        if not filepath:
            return
            
        try:
            strategy_name = self.data_manager.import_file(filepath)
            
            if strategy_name:
                # Analyze the new strategy
                self.analyzer.analyze_strategy(strategy_name)
                
                # Refresh the strategy list
                self.refresh_strategies()
                
                # Update analytics combo
                self.update_analytics_combo()
                
                messagebox.showinfo("Import Successful", f"Successfully imported strategy: {strategy_name}")
            else:
                messagebox.showerror("Import Failed", "Failed to import strategy")
                
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing file: {str(e)}")

    def refresh_strategies(self):
        """Refresh the strategy list"""
        # Clear the treeview
        for item in self.strategy_tree.get_children():
            self.strategy_tree.delete(item)
            
        # Add strategies to the treeview
        for strategy_name, metrics in self.analyzer.strategy_metrics.items():
            # Get the strategy data
            strategy_data = self.data_manager.strategy_data.get(strategy_name)
            num_trades = len(strategy_data) if strategy_data is not None else 0
            
            win_rate = f"{metrics['win_rate'] * 100:.1f}%"
            total_pnl = f"₹{metrics['total_pnl']:.2f}"
            
            # Add to treeview
            self.strategy_tree.insert("", "end", values=(strategy_name, num_trades, win_rate, total_pnl))
        
        # Update analytics combo
        self.update_analytics_combo()

    def view_strategy_data(self):
        """View the data for the selected strategy"""
        selected_items = self.strategy_tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a strategy to view")
            return
            
        item = selected_items[0]
        values = self.strategy_tree.item(item, "values")
        strategy_name = values[0]
        
        # Get the strategy data
        strategy_data = self.data_manager.strategy_data.get(strategy_name)
        if strategy_data is None:
            messagebox.showinfo("No Data", f"No data available for strategy: {strategy_name}")
            return
        
        # Create a new window to display the data
        data_window = tk.Toplevel(self.root)
        data_window.title(f"Strategy Data: {strategy_name}")
        data_window.geometry("800x600")
        
        # Create a frame for the treeview
        tree_frame = ttk.Frame(data_window)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame)
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Create columns for the treeview
        columns = list(strategy_data.columns)
        
        # Create the treeview
        data_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Configure scrollbars
        y_scrollbar.config(command=data_tree.yview)
        x_scrollbar.config(command=data_tree.xview)
        
        # Configure columns and headings
        for col in columns:
            data_tree.column(col, width=100, anchor="center")
            data_tree.heading(col, text=col)
        
        # Add data to the treeview
        for _, row in strategy_data.iterrows():
            values = [row[col] for col in columns]
            data_tree.insert("", "end", values=values)
        
        data_tree.pack(fill="both", expand=True)

    def remove_strategy(self):
        """Remove the selected strategy"""
        selected_items = self.strategy_tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a strategy to remove")
            return
            
        item = selected_items[0]
        values = self.strategy_tree.item(item, "values")
        strategy_name = values[0]
        
        # Confirm removal
        confirm = messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove strategy: {strategy_name}?")
        if not confirm:
            return
        
        try:
            # Remove strategy from data manager
            if strategy_name in self.data_manager.strategy_data:
                del self.data_manager.strategy_data[strategy_name]
            
            # Remove strategy from analyzer
            if strategy_name in self.analyzer.strategy_metrics:
                del self.analyzer.strategy_metrics[strategy_name]
                
            if strategy_name in self.analyzer.vix_range_performance:
                del self.analyzer.vix_range_performance[strategy_name]
                
            if strategy_name in self.analyzer.monthly_performance:
                del self.analyzer.monthly_performance[strategy_name]
            
            # Refresh the strategy list
            self.refresh_strategies()
            
            # Update analytics combo
            self.update_analytics_combo()
            
            messagebox.showinfo("Removal Successful", f"Successfully removed strategy: {strategy_name}")
            
        except Exception as e:
            messagebox.showerror("Removal Error", f"Error removing strategy: {str(e)}")

    def update_analytics_combo(self):
        """Update the analytics strategy combo"""
        strategies = list(self.analyzer.strategy_metrics.keys())
        self.analytics_strategy_combo['values'] = strategies
        if strategies:
            self.analytics_strategy_var.set(strategies[0])

    def analyze_strategy(self):
        """Analyze the selected strategy"""
        strategy_name = self.analytics_strategy_var.get()
        if not strategy_name:
            messagebox.showinfo("No Selection", "Please select a strategy to analyze")
            return
        
        # Get strategy data and metrics
        strategy_data = self.data_manager.strategy_data.get(strategy_name)
        metrics = self.analyzer.strategy_metrics.get(strategy_name)
        vix_perf = self.analyzer.vix_range_performance.get(strategy_name)
        monthly_perf = self.analyzer.monthly_performance.get(strategy_name)
        
        if strategy_data is None or metrics is None:
            messagebox.showinfo("No Data", f"No data available for strategy: {strategy_name}")
            return
        
        # Generate analytics
        # Overview tab
        self.generate_overview_analytics(strategy_name, strategy_data, metrics)
        
        # VIX analysis tab
        self.generate_vix_analytics(strategy_name, strategy_data, vix_perf)
        
        # Monthly analysis tab
        self.generate_monthly_analytics(strategy_name, strategy_data, monthly_perf)
        
        # Correlations tab
        self.generate_correlation_analytics(strategy_name, strategy_data, metrics)

    def generate_overview_analytics(self, strategy_name, data, metrics):
        """Generate overview analytics for the strategy"""
        # Clear the figure
        self.overview_fig.clear()
        
        # Create subplots
        gs = self.overview_fig.add_gridspec(2, 2)
        ax1 = self.overview_fig.add_subplot(gs[0, 0])  # P&L histogram
        ax2 = self.overview_fig.add_subplot(gs[0, 1])  # Win rate pie chart
        ax3 = self.overview_fig.add_subplot(gs[1, :])  # Cumulative P&L
        
        # P&L histogram
        ax1.hist(data['pnl'], bins=20, color='skyblue', edgecolor='black')
        ax1.set_title('P&L Distribution')
        ax1.set_xlabel('P&L (₹)')
        ax1.set_ylabel('Frequency')
        ax1.axvline(0, color='red', linestyle='--')
        
        # Win rate pie chart
        win_rate = metrics['win_rate']
        ax2.pie([win_rate, 1-win_rate], labels=['Win', 'Loss'], autopct='%1.1f%%', 
                colors=['#a8e6cf', '#ffaaa5'], explode=(0.1, 0))
        ax2.set_title('Win/Loss Ratio')
        
        # Cumulative P&L
        data_sorted = data.sort_values('date')
        cumulative_pnl = data_sorted['pnl'].cumsum()
        
        ax3.plot(range(len(cumulative_pnl)), cumulative_pnl, marker='o', markersize=3)
        ax3.set_title('Cumulative P&L')
        ax3.set_xlabel('Trade #')
        ax3.set_ylabel('Cumulative P&L (₹)')
        ax3.axhline(0, color='gray', linestyle='--')
        ax3.grid(True, linestyle='--', alpha=0.7)
        
        # Add key metrics as text
        metrics_text = (
            f"Total P&L: ₹{metrics['total_pnl']:.2f}\n"
            f"Win Rate: {metrics['win_rate']*100:.1f}%\n"
            f"Avg Profit: ₹{metrics['avg_profit']:.2f}\n"
            f"Avg Loss: ₹{metrics['avg_loss']:.2f}\n"
            f"Profit Factor: {metrics['profit_factor']:.2f}"
        )
        self.overview_fig.text(0.02, 0.02, metrics_text, fontsize=10, 
                              bbox=dict(facecolor='white', alpha=0.8))
        
        # Add title
        self.overview_fig.suptitle(f"Strategy Overview: {strategy_name}", fontsize=14)
        
        # Adjust layout
        self.overview_fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Draw the canvas
        self.overview_canvas.draw()

    def generate_vix_analytics(self, strategy_name, data, vix_perf):
        """Generate VIX-based analytics for the strategy"""
        # Clear the figure
        self.vix_fig.clear()
        
        # Create subplots
        gs = self.vix_fig.add_gridspec(2, 2)
        ax1 = self.vix_fig.add_subplot(gs[0, 0])  # VIX range vs P&L scatter
        ax2 = self.vix_fig.add_subplot(gs[0, 1])  # VIX category performance
        ax3 = self.vix_fig.add_subplot(gs[1, 0])  # Win rate by VIX category
        ax4 = self.vix_fig.add_subplot(gs[1, 1])  # Avg P&L by VIX category
        
        # VIX range vs P&L scatter
        ax1.scatter(data['prev_vix_range'], data['pnl'], alpha=0.6)
        ax1.set_title('VIX Range vs P&L')
        ax1.set_xlabel('Previous Day VIX Range')
        ax1.set_ylabel('P&L (₹)')
        ax1.axhline(0, color='gray', linestyle='--')
        
        # Add trend line
        if len(data) > 1:
            z = np.polyfit(data['prev_vix_range'], data['pnl'], 1)
            p = np.poly1d(z)
            ax1.plot(data['prev_vix_range'], p(data['prev_vix_range']), "r--")
        
        # VIX category performance
        if vix_perf:
            categories = []
            counts = []
            for category, perf in sorted(vix_perf.items(), key=lambda x: get_vix_category_order(x[0])):
                categories.append(category)
                counts.append(perf['count'])
            
            ax2.bar(categories, counts, color='skyblue')
            ax2.set_title('Number of Trades by VIX Category')
            ax2.set_xlabel('VIX Category')
            ax2.set_ylabel('Number of Trades')
            ax2.tick_params(axis='x', rotation=45)
            
            # Win rate by VIX category
            win_rates = [perf['win_rate'] * 100 for _, perf in sorted(vix_perf.items(), key=lambda x: get_vix_category_order(x[0]))]
            ax3.bar(categories, win_rates, color='#a8e6cf')
            ax3.set_title('Win Rate by VIX Category')
            ax3.set_xlabel('VIX Category')
            ax3.set_ylabel('Win Rate (%)')
            ax3.tick_params(axis='x', rotation=45)
            ax3.set_ylim(0, 100)
            
            # Avg P&L by VIX category
            avg_pnls = [perf['avg_pnl'] for _, perf in sorted(vix_perf.items(), key=lambda x: get_vix_category_order(x[0]))]
            colors = ['green' if pnl > 0 else 'red' for pnl in avg_pnls]
            ax4.bar(categories, avg_pnls, color=colors)
            ax4.set_title('Avg P&L by VIX Category')
            ax4.set_xlabel('VIX Category')
            ax4.set_ylabel('Avg P&L (₹)')
            ax4.tick_params(axis='x', rotation=45)
            ax4.axhline(0, color='gray', linestyle='--')
        
        # Add title
        self.vix_fig.suptitle(f"VIX Analysis: {strategy_name}", fontsize=14)
        
        # Adjust layout
        self.vix_fig.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Draw the canvas
        self.vix_canvas.draw()

    def generate_monthly_analytics(self, strategy_name, data, monthly_perf):
        """Generate monthly analytics for the strategy"""
        # Clear the figure
        self.monthly_fig.clear()
        
        # Create subplots
        gs = self.monthly_fig.add_gridspec(2, 2)
        ax1 = self.monthly_fig.add_subplot(gs[0, 0])  # Trades by month
        ax2 = self.monthly_fig.add_subplot(gs[0, 1])  # Win rate by month
        ax3 = self.monthly_fig.add_subplot(gs[1, :])  # Avg P&L by month
        
        if monthly_perf:
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            months = list(range(1, 13))
            
            # Prepare data
            counts = [monthly_perf.get(m, {}).get('count', 0) for m in months]
            win_rates = [monthly_perf.get(m, {}).get('win_rate', 0) * 100 for m in months]
            avg_pnls = [monthly_perf.get(m, {}).get('avg_pnl', 0) for m in months]
            
            # Trades by month
            ax1.bar(month_names, counts, color='skyblue')
            ax1.set_title('Number of Trades by Month')
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Number of Trades')
            
            # Win rate by month
            ax2.bar(month_names, win_rates, color='#a8e6cf')
            ax2.set_title('Win Rate by Month')
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Win Rate (%)')
            ax2.set_ylim(0, 100)
            
            # Avg P&L by month
            colors = ['green' if pnl > 0 else 'red' for pnl in avg_pnls]
            bars = ax3.bar(month_names, avg_pnls, color=colors)
            ax3.set_title('Average P&L by Month')
            ax3.set_xlabel('Month')
            ax3.set_ylabel('Avg P&L (₹)')
            ax3.axhline(0, color='gray', linestyle='--')
            
            # Add P&L values on top of bars
            for bar, pnl in zip(bars, avg_pnls):
                if pnl != 0:
                    height = bar.get_height()
                    text_height = height + 1000 if height > 0 else height - 5000
                    ax3.text(bar.get_x() + bar.get_width()/2., text_height,
                            f'₹{pnl:.0f}', ha='center', va='bottom', rotation=0)
        
        # Add title
        self.monthly_fig.suptitle(f"Monthly Analysis: {strategy_name}", fontsize=14)
        
        # Adjust layout
        self.monthly_fig.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Draw the canvas
        self.monthly_canvas.draw()

    def generate_correlation_analytics(self, strategy_name, data, metrics):
        """Generate correlation analytics for the strategy"""
        # Clear the figure
        self.corr_fig.clear()
        
        # Create subplots
        gs = self.corr_fig.add_gridspec(2, 2)
        ax1 = self.corr_fig.add_subplot(gs[0, 0])  # VIX range correlation
        ax2 = self.corr_fig.add_subplot(gs[0, 1])  # Index range correlation
        ax3 = self.corr_fig.add_subplot(gs[1, :])  # Correlation matrix
        
        # VIX range correlation
        ax1.scatter(data['prev_vix_range'], data['pnl'], alpha=0.6)
        ax1.set_title('P&L vs Previous Day VIX Range')
        ax1.set_xlabel('Previous Day VIX Range')
        ax1.set_ylabel('P&L (₹)')
        ax1.axhline(0, color='gray', linestyle='--')
        
        # Add trend line and correlation coefficient
        if len(data) > 1:
            z = np.polyfit(data['prev_vix_range'], data['pnl'], 1)
            p = np.poly1d(z)
            ax1.plot(data['prev_vix_range'], p(data['prev_vix_range']), "r--")
            
            corr = data['prev_vix_range'].corr(data['pnl'])
            ax1.annotate(f"Correlation: {corr:.2f}", xy=(0.05, 0.95), xycoords='axes fraction',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
        
        # Index range correlation


    # Index range correlation
        ax2.scatter(data['prev_index_range'], data['pnl'], alpha=0.6)
        ax2.set_title('P&L vs Previous Day Index Range')
        ax2.set_xlabel('Previous Day Index Range')
        ax2.set_ylabel('P&L (₹)')
        ax2.axhline(0, color='gray', linestyle='--')
        
        # Add trend line and correlation coefficient
        if len(data) > 1:
            z = np.polyfit(data['prev_index_range'], data['pnl'], 1)
            p = np.poly1d(z)
            ax2.plot(data['prev_index_range'], p(data['prev_index_range']), "r--")
            
            corr = data['prev_index_range'].corr(data['pnl'])
            ax2.annotate(f"Correlation: {corr:.2f}", xy=(0.05, 0.95), xycoords='axes fraction',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
        
        # Correlation matrix
        if len(data) > 1:
            # Select relevant columns for correlation
            corr_columns = ['pnl', 'prev_vix_range', 'prev_index_range']
            corr_data = data[corr_columns].copy()
            
            # Rename columns for better display
            corr_data.columns = ['P&L', 'VIX Range', 'Index Range']
            
            # Calculate correlation matrix
            corr_matrix = corr_data.corr()
            
            # Create heatmap
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=ax3)
            ax3.set_title('Correlation Matrix')
        
        # Add title
        self.corr_fig.suptitle(f"Correlation Analysis: {strategy_name}", fontsize=14)
        
        # Adjust layout
        self.corr_fig.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Draw the canvas
        self.corr_canvas.draw()

    def browse_data_dir(self):
        """Browse for data directory"""
        directory = filedialog.askdirectory(title="Select Data Directory")
        if directory:
            self.data_dir_entry.delete(0, tk.END)
            self.data_dir_entry.insert(0, directory)

    def save_settings(self):
        """Save application settings"""
        # Get data directory
        data_dir = self.data_dir_entry.get()
        
        # Validate directory
        if not os.path.exists(data_dir):
            create_dir = messagebox.askyesno("Directory Not Found", 
                                             f"Directory '{data_dir}' does not exist. Create it?")
            if create_dir:
                try:
                    os.makedirs(data_dir)
                except:
                    messagebox.showerror("Error", f"Failed to create directory: {data_dir}")
                    return
            else:
                return
        
        # Update data manager
        old_dir = self.data_manager.data_directory
        self.data_manager.data_directory = data_dir
        
        # Move files if needed
        if old_dir != data_dir and os.path.exists(old_dir):
            move_files = messagebox.askyesno("Move Files", 
                                             f"Move existing strategy files from '{old_dir}' to '{data_dir}'?")
            if move_files:
                try:
                    # Create new directory if it doesn't exist
                    if not os.path.exists(data_dir):
                        os.makedirs(data_dir)
                    
                    # Move files
                    import shutil
                    for filename in os.listdir(old_dir):
                        if filename.endswith('.xlsx') or filename.endswith('.xls'):
                            src = os.path.join(old_dir, filename)
                            dst = os.path.join(data_dir, filename)
                            shutil.copy2(src, dst)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to move files: {str(e)}")
        
        # Reload data
        self.load_data()
        
        messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")

    def get_vix_category_order(category):
        """Helper function to get the order of VIX categories"""
        order = {
            'Very Low': 0,
            'Low': 1,
            'Medium': 2,
            'High': 3,
            'Very High': 4
        }
        return order.get(category, 999)

    def main():
        root = tk.Tk()
        app = StrategySelectionApp(root)
        root.mainloop()

    if __name__ == "__main__":
        main()