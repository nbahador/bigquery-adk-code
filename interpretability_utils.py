import pandas as pd
import numpy as np
from typing import Dict, List, Any
import json
import datetime
import hashlib

class MechanisticInterpreter:
    """Utility class for mechanistic interpretability analysis"""
    
    VALID_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    }
    
    @staticmethod
    def validate_claim_data(claim_data: Dict) -> Dict:
        """Validate claim data with bounds checking"""
        errors = []
        
        # Validate amount
        amount = claim_data.get('claim_amount', 0)
        if not (1 <= amount <= 10000):
            errors.append(f"Invalid claim amount: ${amount}. Must be between $1 and $10,000")
        
        # Validate state
        state = claim_data.get('patient_state', '').upper()
        if state not in MechanisticInterpreter.VALID_STATES:
            errors.append(f"Invalid state code: {state}")
        
        # Validate procedure type
        valid_procedures = {'Virtual Consultation', 'Mental Health Session', 
                           'Prescription Refill', 'Follow-up Visit', 'Emergency Consult'}
        procedure = claim_data.get('procedure_type')
        if procedure and procedure not in valid_procedures:
            errors.append(f"Invalid procedure type: {procedure}")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    @staticmethod
    def analyze_claim_features(claim_data: Dict) -> Dict:
        """Analyze individual claim features against normal ranges"""
        procedure_norms = {
            'Virtual Consultation': {'avg': 150, 'std': 45, 'max_normal': 450},
            'Mental Health Session': {'avg': 200, 'std': 60, 'max_normal': 600},
            'Prescription Refill': {'avg': 50, 'std': 15, 'max_normal': 150},
            'Follow-up Visit': {'avg': 120, 'std': 36, 'max_normal': 360},
            'Emergency Consult': {'avg': 300, 'std': 90, 'max_normal': 900}
        }
        
        diagnosis_categories = {
            'Mental Health': ['Anxiety', 'Depression', 'Insomnia'],
            'Physical': ['Hypertension', 'Diabetes', 'Common Cold', 'Back Pain', 
                        'Migraine', 'Allergies', 'Stomach Flu']
        }
        
        analysis = {
            'procedure_analysis': {},
            'diagnosis_analysis': {},
            'amount_analysis': {},
            'geographic_analysis': {}
        }
        
        # Procedure analysis
        procedure = claim_data.get('procedure_type')
        if procedure in procedure_norms:
            norm = procedure_norms[procedure]
            amount = claim_data.get('claim_amount', 0)
            analysis['procedure_analysis'] = {
                'expected_range': f"${norm['avg'] - norm['std']} - ${norm['avg'] + norm['std']}",
                'actual_amount': f"${amount}",
                'deviation_sigma': (amount - norm['avg']) / norm['std'] if norm['std'] > 0 else 0,
                'threshold_violation': amount > norm['max_normal']
            }
        
        # Diagnosis-procedure compatibility
        diagnosis = claim_data.get('diagnosis')
        analysis['diagnosis_analysis'] = {
            'diagnosis_category': next((cat for cat, diags in diagnosis_categories.items() 
                                      if diagnosis in diags), 'Unknown'),
            'typical_procedures': 'Mental Health procedures typically for Mental Health diagnoses'
        }
        
        return analysis
    
    @staticmethod
    def evaluate_business_rules(claim_data: Dict) -> List[Dict]:
        """Evaluate which business rules are activated for a claim"""
        rules_activated = []
        
        # Rule 1: Unusual diagnosis-procedure combinations
        unusual_combos = [
            ('Mental Health Session', 'Common Cold'),
            ('Mental Health Session', 'Back Pain'),
            ('Emergency Consult', 'Allergies'),
            ('Emergency Consult', 'Common Cold')
        ]
        
        procedure = claim_data.get('procedure_type')
        diagnosis = claim_data.get('diagnosis')
        
        if (procedure, diagnosis) in unusual_combos:
            rules_activated.append({
                'rule_id': 'UNUSUAL_COMBO',
                'description': f'Unusual combination: {procedure} + {diagnosis}',
                'confidence': 'High',
                'evidence': 'Combination statistically rare in historical data'
            })
        
        # Rule 2: High claim amount
        procedure_norms = {
            'Virtual Consultation': 450,
            'Mental Health Session': 600,
            'Prescription Refill': 150,
            'Follow-up Visit': 360,
            'Emergency Consult': 900
        }
        
        amount = claim_data.get('claim_amount', 0)
        threshold = procedure_norms.get(procedure, float('inf'))
        
        if amount > threshold:
            rules_activated.append({
                'rule_id': 'HIGH_AMOUNT',
                'description': f'Claim amount ${amount} exceeds ${threshold} threshold',
                'confidence': 'High' if amount > threshold * 1.5 else 'Medium',
                'evidence': f'{amount/threshold*100:.1f}% above expected maximum'
            })
        
        # Rule 3: Geographic mismatch
        restricted_states = ['WY', 'AK', 'MT']
        state = claim_data.get('patient_state')
        
        if state in restricted_states and procedure == 'Virtual Consultation':
            rules_activated.append({
                'rule_id': 'GEOGRAPHIC_RESTRICTION',
                'description': f'Virtual consultation from restricted state: {state}',
                'confidence': 'High',
                'evidence': 'State not covered for virtual consultations'
            })
        
        return rules_activated
    
    @staticmethod
    def generate_interpretability_report(claim_data: Dict, similar_claims: List[Dict]) -> Dict:
        """Generate comprehensive interpretability report"""
        feature_analysis = MechanisticInterpreter.analyze_claim_features(claim_data)
        rules_activated = MechanisticInterpreter.evaluate_business_rules(claim_data)
        
        report = {
            'claim_id': claim_data.get('claim_id'),
            'feature_analysis': feature_analysis,
            'rules_activated': rules_activated,
            'decision_pathway': MechanisticInterpreter.trace_decision_pathway(rules_activated),
            'confidence_assessment': MechanisticInterpreter.assess_confidence(rules_activated),
            'similar_patterns': len(similar_claims),
            'recommendations': MechanisticInterpreter.generate_recommendations(rules_activated),
            'counterfactuals': MechanisticInterpreter.generate_counterfactuals(claim_data)
        }
        
        return report
    
    @staticmethod
    def trace_decision_pathway(rules_activated: List[Dict]) -> List[str]:
        """Trace the decision-making pathway"""
        pathway = []
        
        if any(rule['rule_id'] == 'UNUSUAL_COMBO' for rule in rules_activated):
            pathway.append("Primary trigger: Unusual diagnosis-procedure combination")
        
        if any(rule['rule_id'] == 'HIGH_AMOUNT' for rule in rules_activated):
            pathway.append("Supporting factor: Abnormally high claim amount")
        
        if any(rule['rule_id'] == 'GEOGRAPHIC_RESTRICTION' for rule in rules_activated):
            pathway.append("Geographic constraint violation")
        
        return pathway
    
    @staticmethod
    def assess_confidence(rules_activated: List[Dict]) -> Dict:
        """Assess confidence level for outlier detection"""
        high_conf_rules = sum(1 for rule in rules_activated if rule['confidence'] == 'High')
        total_rules = len(rules_activated)
        
        if total_rules == 0:
            return {'level': 'Low', 'score': 0, 'reason': 'No rules activated'}
        
        confidence_score = high_conf_rules / total_rules
        
        if confidence_score >= 0.7:
            level = 'High'
        elif confidence_score >= 0.4:
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'level': level,
            'score': confidence_score,
            'reason': f'{high_conf_rules} high-confidence rules out of {total_rules} total'
        }
    
    @staticmethod
    def generate_recommendations(rules_activated: List[Dict]) -> List[str]:
        """Generate human review recommendations"""
        recommendations = []
        
        if any(rule['rule_id'] == 'UNUSUAL_COMBO' for rule in rules_activated):
            recommendations.append("Review medical necessity of procedure-diagnosis combination")
        
        if any(rule['rule_id'] == 'HIGH_AMOUNT' for rule in rules_activated):
            recommendations.append("Verify procedure coding and duration justification")
        
        if any(rule['rule_id'] == 'GEOGRAPHIC_RESTRICTION' for rule in rules_activated):
            recommendations.append("Confirm patient residency and coverage eligibility")
        
        return recommendations
    
    @staticmethod
    def check_demographic_fairness(claims_df: pd.DataFrame) -> Dict:
        """Monitor fairness across demographics"""
        fairness_report = {}
        
        # Check outlier rates by state
        if 'is_outlier' in claims_df.columns and 'patient_state' in claims_df.columns:
            state_outlier_rates = claims_df.groupby('patient_state')['is_outlier'].mean()
            fairness_report['state_disparities'] = {
                'max_rate': state_outlier_rates.max(),
                'min_rate': state_outlier_rates.min(),
                'ratio': state_outlier_rates.max() / state_outlier_rates.min() if state_outlier_rates.min() > 0 else float('inf')
            }
        
        # Check by provider
        if 'is_outlier' in claims_df.columns and 'provider_name' in claims_df.columns:
            provider_rates = claims_df.groupby('provider_name')['is_outlier'].mean()
            fairness_report['provider_disparities'] = {
                'max_rate': provider_rates.max(),
                'min_rate': provider_rates.min(),
                'ratio': provider_rates.max() / provider_rates.min() if provider_rates.min() > 0 else float('inf')
            }
        
        return fairness_report
    
    @staticmethod
    def generate_disparity_alerts(fairness_report: Dict) -> List[str]:
        """Generate alerts for systematic disparities"""
        alerts = []
        
        state_ratio = fairness_report.get('state_disparities', {}).get('ratio', 1.0)
        provider_ratio = fairness_report.get('provider_disparities', {}).get('ratio', 1.0)
        
        if state_ratio > 2.0:
            alerts.append(f"HIGH DISPARITY: State outlier rates vary by {state_ratio:.2f}x")
        
        if provider_ratio > 3.0:
            alerts.append(f"HIGH DISPARITY: Provider outlier rates vary by {provider_ratio:.2f}x")
        
        return alerts
    
    @staticmethod
    def generate_counterfactuals(claim_data: Dict) -> List[str]:
        """Generate counterfactual explanations"""
        counterfactuals = []
        current_amount = claim_data.get('claim_amount', 0)
        procedure = claim_data.get('procedure_type')
        
        # Amount-based counterfactuals
        procedure_thresholds = {
            'Virtual Consultation': 450,
            'Mental Health Session': 600,
            'Emergency Consult': 900
        }
        
        threshold = procedure_thresholds.get(procedure)
        if threshold and current_amount > threshold:
            safe_amount = threshold * 0.9
            counterfactuals.append(
                f"If claim amount were ${safe_amount:.2f} instead of ${current_amount}, "
                f"this claim would likely not be flagged as an outlier"
            )
        
        return counterfactuals
    
    @staticmethod
    def create_audit_log(claim_data: Dict, rules_activated: List[Dict], decision: str) -> Dict:
        """Create comprehensive audit log"""
        # Create hash for data integrity
        data_hash = hashlib.md5(json.dumps(claim_data, sort_keys=True).encode()).hexdigest()
        
        audit_entry = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'claim_id': claim_data.get('claim_id'),
            'decision': decision,
            'rules_activated': [rule['rule_id'] for rule in rules_activated],
            'confidence_scores': [rule.get('confidence', 'Unknown') for rule in rules_activated],
            'decision_pathway': MechanisticInterpreter.trace_decision_pathway(rules_activated),
            'system_version': '1.0',
            'audit_hash': data_hash,
            'validation_status': MechanisticInterpreter.validate_claim_data(claim_data)
        }
        return audit_entry