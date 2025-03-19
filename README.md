# Advanced Trading Strategy Analysis

## Overview
This project implements a data-driven trading strategy selection framework that optimizes decision-making based on market conditions. Current win ratio: 63%, target: 75%.

## Strategy Selection Framework

### VIX Range Categories
- Very Low: 0 to <1
- Low: 1 to <1.5
- Medium: 1.5 to <2
- High: 2 to <3
- Very High: 3+

### Decision Score (0-100)
Score combines three components:
1. **VIX Range Score** (0-60 points)
   - Formula: `min(prev_vix_range * 30, 60)`
   
2. **Index Range Score** (0-20 points)
   - Formula: `min(max(20 - (prev_index_range / 20), 0), 20)`
   
3. **Monthly Adjustment** (-20 to +20 points)
   - Strong Positive: October (+20), July (+15)
   - Positive: January/June (+10), March/August (+5)
   - Neutral: May/September/November (0)
   - Negative: December (-10)
   - Strong Negative: February (-15), April (-20)

### Recommendation Thresholds
- **HIGHLY RECOMMENDED**: Score ≥ 70, Position Size: 100%
- **RECOMMENDED**: Score 60-69, Position Size: 75%
- **NEUTRAL**: Score 50-59, Position Size: 50%
- **NOT RECOMMENDED**: Score < 50, Position Size: 0%

## Strategy Performance Analysis

### Strategy 1 (52_wop_0.5_nifty)
- Win Rate: 43.86%
- Profit Factor: 2.38
- Best Environment: High VIX (2-3), Oct/Jul/May
- SQN Rating: 2.2 (Average quality system)
- VIX Correlation: Strong positive in High VIX range (SQN 3.4)

### Strategy 2 (54_wop_0.2_nifty)
- Win Rate: 61.40%
- Profit Factor: 1.41
- Best Environment: Medium VIX (1.5-2), Oct/Jul/May
- SQN Rating: 2.6 (Average quality system)
- VIX Correlation: Strong positive in Medium VIX range (SQN 3.8)

## Key Insights

### Optimal Strategy Selection
- Use Strategy 1 in High VIX range (2-3)
- Use Strategy 2 in Medium (1.5-2) and Very High (3+) VIX ranges

### Monthly Patterns
- October: Both strategies show 100% win rate (SQN >4.0)
- April: Both strategies show 25% win rate (SQN <0.7)
- Strategy 2 outperforms in January, March, June, and December

### Market Condition Impact
- Negative correlation with Index Range (-0.36 to -0.41)
- Positive correlation with Current Day VIX Range

## Position Sizing by SQN Quality
- Good SQN (3.0+): 100% position
- Average SQN (2.0-2.9): 75% position
- Below Average SQN (1.0-1.9): 50% position
- Poor SQN (<1.0): Avoid or minimal position

## Implementation
The framework converts subjective trading decisions into a quantifiable process by:
1. Checking previous day's VIX and index ranges each morning
2. Applying the scoring system to determine strategy selection
3. Adjusting position sizes based on confidence score
4. Tracking actual vs. predicted performance to refine the model

This systematic approach aims to improve the current 63% win ratio to the target 75%.
