import logging
from typing import Any

logger = logging.getLogger(__name__)

CATEGORY_METADATA = {
    'publications': {
        'label': 'Publications',
        'description': 'Peer-reviewed scholarly articles',
        'eb1_weight': 'High',
        'eb2_weight': 'Medium',
        'min_for_eb1': 8,
        'min_for_eb2': 4,
        'impact': 'Demonstrates original contribution to field'
    },
    'citations': {
        'label': 'Citations',
        'description': 'Times your work was cited by others',
        'eb1_weight': 'High',
        'eb2_weight': 'Medium',
        'min_for_eb1': 10,
        'min_for_eb2': 5,
        'impact': 'Evidence of influence and recognition by peers'
    },
    'awards': {
        'label': 'Awards',
        'description': 'Nationally/internationally recognized prizes',
        'eb1_weight': 'High',
        'eb2_weight': 'Medium',
        'min_for_eb1': 10,
        'min_for_eb2': 0,
        'impact': 'Third-party validation of excellence'
    },
    'media': {
        'label': 'Media Coverage',
        'description': 'Coverage in major publications',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Low',
        'min_for_eb1': 10,
        'min_for_eb2': 0,
        'impact': 'Demonstrates public recognition'
    },
    'judging': {
        'label': 'Peer Review',
        'description': 'Judging work of others in the field',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Low',
        'min_for_eb1': 10,
        'min_for_eb2': 0,
        'impact': 'Peer recognition and expertise validation'
    },
    'leadership': {
        'label': 'Leadership',
        'description': 'Leadership in critical/specialized organizations',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Medium',
        'min_for_eb1': 10,
        'min_for_eb2': 5,
        'impact': 'Demonstrates extraordinary capability'
    },
    'salary': {
        'label': 'High Salary',
        'description': 'Compensation significantly above peers',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Medium',
        'min_for_eb1': 10,
        'min_for_eb2': 5,
        'impact': 'Market validation of exceptional ability'
    },
    'memberships': {
        'label': 'Exclusive Memberships',
        'description': 'Membership in exclusive organizations',
        'eb1_weight': 'Low',
        'eb2_weight': 'Low',
        'min_for_eb1': 5,
        'min_for_eb2': 0,
        'impact': 'Peer recognition indicator'
    },
    'recommendations': {
        'label': 'Recommendations',
        'description': 'Expert recommendation letters',
        'eb1_weight': 'High',
        'eb2_weight': 'High',
        'min_for_eb1': 10,
        'min_for_eb2': 10,
        'impact': 'Critical supporting evidence from peers'
    },
    'speaking': {
        'label': 'Speaking Engagements',
        'description': 'Conference presentations',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Low',
        'min_for_eb1': 5,
        'min_for_eb2': 0,
        'impact': 'Demonstrates expertise dissemination'
    },
    'patents': {
        'label': 'Patents/IP',
        'description': 'Patents or proprietary contributions',
        'eb1_weight': 'Medium',
        'eb2_weight': 'Medium',
        'min_for_eb1': 10,
        'min_for_eb2': 5,
        'impact': 'Evidence of original contributions'
    },
    'endeavor': {
        'label': 'Proposed Endeavor',
        'description': 'National importance of proposed work',
        'eb1_weight': 'High',
        'eb2_weight': 'High',
        'min_for_eb1': 5,
        'min_for_eb2': 5,
        'impact': 'Core requirement for petition approval'
    }
}


class AIContextBuilder:
    
    def prepare_ai_context(self, submission: Any, scores: dict) -> dict:
        raw = submission.raw_answers or {}
        category_scores = scores.get('category_scores', {})
        
        context = {
            'strengths': self._analyze_strengths(category_scores, raw),
            'gaps': self._analyze_gaps(category_scores, raw),
            'risk_flags': self._identify_risk_flags(category_scores, raw, scores),
            'recommended_focus': self._determine_focus_areas(category_scores, scores),
            'eb1_alignment': self._assess_eb1_alignment(category_scores),
            'eb2_alignment': self._assess_eb2_alignment(category_scores),
            'petition_recommendation': self._recommend_petition_type(submission, scores),
            'raw_highlights': self._extract_raw_highlights(raw),
            'scoring_summary': self._generate_scoring_summary(scores)
        }
        
        return context
    
    def _analyze_strengths(self, category_scores: dict, raw: dict) -> list:
        strengths = []
        
        for category, score in category_scores.items():
            meta = CATEGORY_METADATA.get(category, {})
            max_score = meta.get('min_for_eb1', 10)
            
            if score > 0 and score >= max_score:
                percent = (score / max_score * 100) if max_score > 0 else 0
                
                strength = {
                    'category': category,
                    'label': meta.get('label', category.title()),
                    'score': score,
                    'max_score': max_score,
                    'percent': min(percent, 100),
                    'eb1_relevance': meta.get('eb1_weight', 'Low'),
                    'impact': meta.get('impact', ''),
                    'raw_value': self._get_raw_display_value(raw, category),
                    'guidance': self._get_strength_guidance(category, score, raw)
                }
                strengths.append(strength)
        
        return sorted(strengths, key=lambda x: x['score'], reverse=True)
    
    def _analyze_gaps(self, category_scores: dict, raw: dict) -> list:
        gaps = []
        
        critical_categories = ['publications', 'citations', 'awards', 'recommendations', 'endeavor']
        
        for category in category_scores.keys():
            meta = CATEGORY_METADATA.get(category, {})
            score = category_scores.get(category, 0)
            min_for_eb1 = meta.get('min_for_eb1', 10)
            
            if score < min_for_eb1:
                gap = {
                    'category': category,
                    'label': meta.get('label', category.title()),
                    'current_score': score,
                    'required_for_eb1': min_for_eb1,
                    'deficiency': min_for_eb1 - score,
                    'severity': self._calculate_severity(score, min_for_eb1, category in critical_categories),
                    'description': meta.get('description', ''),
                    'impact': meta.get('impact', ''),
                    'raw_value': self._get_raw_display_value(raw, category),
                    'remediation': self._get_gap_remediation(category, score, raw)
                }
                gaps.append(gap)
        
        return sorted(gaps, key=lambda x: (x['severity'] == 'Critical', x['deficiency']), reverse=True)
    
    def _identify_risk_flags(self, category_scores: dict, raw: dict, scores: dict) -> list:
        risk_flags = []
        total_score = scores.get('total_score', 0)
        
        if category_scores.get('publications', 0) == 0:
            risk_flags.append({
                'type': 'MISSING_PUBLICATIONS',
                'severity': 'HIGH',
                'message': 'No peer-reviewed publications yet. Building a publication record is key for strengthening this case.',
                'consultation_tip': 'We can discuss strategies for accelerating your research output.'
            })
        
        if category_scores.get('citations', 0) == 0:
            risk_flags.append({
                'type': 'MISSING_CITATIONS',
                'severity': 'HIGH',
                'message': "Citation impact isn't showing yet. Building this takes time, but there are strategies.",
                'consultation_tip': 'We can share approaches that have worked for others in your field.'
            })
        
        if category_scores.get('recommendations', 0) == 0:
            risk_flags.append({
                'type': 'MISSING_RECOMMENDATIONS',
                'severity': 'HIGH',
                'message': "Strong recommendation letters aren't in place yet. These are crucial supporting evidence.",
                'consultation_tip': 'We can help identify the right recommenders and guide the letter process.'
            })
        
        if total_score < 40:
            risk_flags.append({
                'type': 'DEVELOPING_PROFILE',
                'severity': 'MEDIUM',
                'message': f'Your score of {total_score} suggests building your profile before filing would be beneficial.',
                'consultation_tip': 'A consultation can help you prioritize which areas to focus on first.'
            })
        
        missing_critical = sum(1 for cat in ['publications', 'citations', 'recommendations'] 
                               if category_scores.get(cat, 0) == 0)
        if missing_critical >= 2:
            risk_flags.append({
                'type': 'BUILDING_CRITERIA',
                'severity': 'MEDIUM',
                'message': f'{missing_critical} key criteria need development. This is common and manageable with a plan.',
                'consultation_tip': 'We can create a realistic timeline for addressing these areas.'
            })
        
        endeavor = raw.get('proposed_endeavor', '')
        if not endeavor or len(endeavor) < 20:
            risk_flags.append({
                'type': 'CLARIFY_ENDEAVOR',
                'severity': 'LOW',
                'message': 'Your proposed endeavor could benefit from more detail and clarity.',
                'consultation_tip': 'We can help articulate the national importance of your work.'
            })
        
        return risk_flags
    
    def _determine_focus_areas(self, category_scores: dict, scores: dict) -> list:
        focus_areas = []
        total_score = scores.get('total_score', 0)
        
        if total_score < 50:
            focus_areas.append({
                'priority': 'FIRST',
                'area': 'Build Your Foundation',
                'action': 'Focus on publications and citations first — these take time but have the biggest impact.',
                'consultation_value': 'We can create a realistic timeline based on your current pace.'
            })
        
        if category_scores.get('publications', 0) < 8:
            focus_areas.append({
                'priority': 'HIGH',
                'area': 'Publication Strategy',
                'action': 'Target quality over quantity — a few strong publications in good journals matter most.',
                'consultation_value': 'We can identify the best venues for your field.'
            })
        
        if category_scores.get('citations', 0) < 10:
            focus_areas.append({
                'priority': 'HIGH',
                'area': 'Build Citation Impact',
                'action': 'Increase visibility through open access, conferences, and collaborations.',
                'consultation_value': 'We can share what has worked for others in your research area.'
            })
        
        if category_scores.get('recommendations', 0) == 0:
            focus_areas.append({
                'priority': 'HIGH',
                'area': 'Secure Strong Letters',
                'action': 'Identify 3-5 experts who can speak specifically to your contributions.',
                'consultation_value': 'We can advise on the best approach for your recommenders.'
            })
        
        if category_scores.get('judging', 0) == 0:
            focus_areas.append({
                'priority': 'MEDIUM',
                'area': 'Peer Review Activity',
                'action': 'Start reviewing for journals or conferences — this builds recognition gradually.',
                'consultation_value': 'We can suggest where to begin.'
            })
        
        if category_scores.get('awards', 0) == 0:
            focus_areas.append({
                'priority': 'MEDIUM',
                'area': 'Award Nominations',
                'action': 'Research relevant awards in your field and ensure you\'re nominated.',
                'consultation_value': 'We can identify awards that strengthen your specific case.'
            })
        
        return focus_areas
    
    def _assess_eb1_alignment(self, category_scores: dict) -> dict:
        required_for_eb1 = ['publications', 'citations', 'awards', 'recommendations']
        met = []
        unmet = []
        
        for cat in required_for_eb1:
            meta = CATEGORY_METADATA.get(cat, {})
            min_score = meta.get('min_for_eb1', 10)
            if category_scores.get(cat, 0) >= min_score:
                met.append(cat)
            else:
                unmet.append(cat)
        
        alignment_score = len(met) / len(required_for_eb1) * 100
        
        return {
            'alignment_score': alignment_score,
            'criteria_met': met,
            'criteria_unmet': unmet,
            'recommendation': 'Strong EB1 candidate' if alignment_score >= 75 else 'May need more evidence' if alignment_score >= 50 else 'Consider EB2 NIW pathway'
        }
    
    def _assess_eb2_alignment(self, category_scores: dict) -> dict:
        core_for_eb2 = ['publications', 'citations', 'endeavor']
        met = []
        unmet = []
        
        for cat in core_for_eb2:
            meta = CATEGORY_METADATA.get(cat, {})
            min_score = meta.get('min_for_eb2', 5)
            if category_scores.get(cat, 0) >= min_score:
                met.append(cat)
            else:
                unmet.append(cat)
        
        alignment_score = len(met) / len(core_for_eb2) * 100
        
        return {
            'alignment_score': alignment_score,
            'criteria_met': met,
            'criteria_unmet': unmet,
            'recommendation': 'Strong NIW candidate' if alignment_score >= 66 else 'May need endeavor refinement' if alignment_score >= 33 else 'Focus on core criteria'
        }
    
    def _recommend_petition_type(self, submission: Any, scores: dict) -> dict:
        total_score = scores.get('total_score', 0)
        category_scores = scores.get('category_scores', {})
        
        eb1_met = sum(1 for cat in ['publications', 'citations', 'awards', 'recommendations']
                      if category_scores.get(cat, 0) >= CATEGORY_METADATA.get(cat, {}).get('min_for_eb1', 10))
        
        eb2_met = sum(1 for cat in ['publications', 'citations', 'endeavor']
                     if category_scores.get(cat, 0) >= CATEGORY_METADATA.get(cat, {}).get('min_for_eb2', 5))
        
        if eb1_met >= 3 and total_score >= 60:
            recommendation = 'EB1A'
            reasoning = 'Strong evidence across multiple EB1A criteria with high total score'
            confidence = 'HIGH'
        elif eb2_met >= 2 and total_score >= 40:
            recommendation = 'EB2_NIW'
            reasoning = 'Adequate evidence for NIW with some EB1A elements present'
            confidence = 'MEDIUM'
        elif eb1_met >= 2 and eb2_met >= 2:
            recommendation = 'BOTH'
            reasoning = 'Profile supports both pathways — pursue EB1A while building NIW case'
            confidence = 'MEDIUM'
        elif eb2_met >= 1:
            recommendation = 'EB2_NIW'
            reasoning = 'Focus on NIW with plan to strengthen for potential EB1A upgrade'
            confidence = 'LOW'
        else:
            recommendation = 'NOT_READY'
            reasoning = 'Multiple criteria gaps require significant development before petition'
            confidence = 'HIGH'
        
        return {
            'recommendation': recommendation,
            'reasoning': reasoning,
            'confidence': confidence,
            'eb1_indicators': eb1_met,
            'eb2_indicators': eb2_met
        }
    
    def _extract_raw_highlights(self, raw: dict) -> dict:
        highlights = {}
        
        if raw.get('field_of_work'):
            highlights['field'] = raw['field_of_work']
        if raw.get('highest_degree'):
            highlights['degree'] = raw['highest_degree']
        if raw.get('publications_count'):
            highlights['publication_count'] = int(raw['publications_count'])
        if raw.get('citations_count'):
            highlights['citation_count'] = int(raw['citations_count'])
        if raw.get('years_experience'):
            highlights['years_experience'] = raw['years_experience']
        if raw.get('proposed_endeavor'):
            endeavor = raw['proposed_endeavor']
            highlights['endeavor_length'] = len(endeavor)
            highlights['endeavor_preview'] = endeavor[:100] + '...' if len(endeavor) > 100 else endeavor
        
        return highlights
    
    def _generate_scoring_summary(self, scores: dict) -> dict:
        return {
            'total_score': scores.get('total_score', 0),
            'max_score': scores.get('max_total', 115),
            'readiness_band': scores.get('readiness_band', 'Unknown'),
            'category_count': len(scores.get('category_scores', {})),
            'top_strengths': [s['category'] for s in scores.get('strongest_categories', [])[:3]],
            'top_gaps': [g['category'] for g in scores.get('weakest_categories', [])[:3]]
        }
    
    def _calculate_severity(self, score: int, required: int, is_critical: bool) -> str:
        deficiency_pct = (required - score) / required if required > 0 else 1
        
        if deficiency_pct >= 1.0:
            return 'CRITICAL' if is_critical else 'HIGH'
        elif deficiency_pct >= 0.5:
            return 'HIGH' if is_critical else 'MEDIUM'
        else:
            return 'MEDIUM' if is_critical else 'LOW'
    
    def _get_raw_display_value(self, raw: dict, category: str) -> str:
        mappings = {
            'publications': raw.get('publications_count', raw.get('has_publications', 'No')),
            'citations': raw.get('citations_count', '0'),
            'awards': raw.get('has_awards', 'No'),
            'media': raw.get('has_media', 'No'),
            'judging': raw.get('has_judging', 'No'),
            'leadership': raw.get('has_leadership', 'No'),
            'salary': raw.get('has_high_salary', 'No'),
            'memberships': raw.get('has_memberships', 'No'),
            'recommendations': raw.get('can_get_letters', 'No'),
            'speaking': raw.get('has_speaking', 'No'),
            'patents': raw.get('has_patents', 'No'),
            'endeavor': raw.get('proposed_endeavor', '')[:50] if raw.get('proposed_endeavor') else 'Not provided'
        }
        return str(mappings.get(category, 'N/A'))
    
    def _get_strength_guidance(self, category: str, score: int, raw: dict) -> str:
        guidance = {
            'publications': f'{score} publications is {"strong" if score >= 10 else "solid"}. Focus on quality and impact metrics.',
            'citations': f'{score} citations shows {"excellent" if score >= 50 else "good"} field recognition. Continue building.',
            'awards': f'Award recognition demonstrates excellence. Ensure documentation is comprehensive.',
            'media': f'Media coverage establishes public recognition. Maximize visibility in relevant outlets.',
            'judging': f'Peer review activity shows standing in field. Maintain consistent engagement.',
            'leadership': f'Leadership experience is valuable. Document specific impact and outcomes.',
            'salary': f'High compensation validates market recognition. Provide comparative evidence.',
            'memberships': f'Exclusive memberships support claims. Ensure proper framing for petition.',
            'recommendations': f'Recommendation letters are critical. Select recommenders strategically.',
            'speaking': f'Conference presence builds visibility. Target key venues in your field.',
            'patents': f'IP contributions demonstrate innovation. Document commercial impact where applicable.',
            'endeavor': f'Endeavor is well-defined. Ensure national importance is clearly articulated.'
        }
        return guidance.get(category, 'Document this strength thoroughly for your petition.')
    
    def _get_gap_remediation(self, category: str, score: int, raw: dict) -> str:
        remediation = {
            'publications': f'Current: {score}. Target: 8+. Consider accelerated publication strategy, target high-impact journals, explore collaborations.',
            'citations': f'Current: {score}. Target: 10+. Increase visibility through open access, conferences, social media for academics, and collaborations.',
            'awards': f'Current: {score}. Target: 10+. Research relevant awards, ensure nominations are submitted, document achievements thoroughly.',
            'media': f'Current: {score}. Target: 10+. Build media presence through press releases, expert commentary, and industry coverage.',
            'judging': f'Current: {score}. Target: 10+. Start reviewing for journals/conferences, join editorial boards over time.',
            'leadership': f'Current: {score}. Target: 10+. Document current leadership, seek opportunities for advancement.',
            'salary': f'Current: {score}. Target: 10+. Gather comparative salary data, document recognition from employers.',
            'memberships': f'Current: {score}. Target: 5+. Research exclusive organizations, ensure achievements meet membership criteria.',
            'recommendations': f'Current: {score}. Target: 10+. Identify 3-5 experts, cultivate relationships, request letters highlighting specific impact.',
            'speaking': f'Current: {score}. Target: 5+. Target key conferences, aim for invited talks, document attendance.',
            'patents': f'Current: {score}. Target: 10+. Document existing IP, pursue new patents where applicable, show commercial impact.',
            'endeavor': f'Current: {len(raw.get("proposed_endeavor", ""))} chars. Target: Clear, detailed articulation of national importance.'
        }
        return remediation.get(category, f'Current: {score}. Develop specific evidence for this criterion.')
