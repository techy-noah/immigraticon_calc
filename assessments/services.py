class ScoringEngine:
    MAX_SCORES = {
        'publications': 15,
        'citations': 15,
        'awards': 10,
        'media': 10,
        'judging': 10,
        'leadership': 10,
        'salary': 10,
        'memberships': 5,
        'recommendations': 10,
        'endeavor': 5
    }

    def __init__(self, raw_answers):
        self.raw_answers = raw_answers

    def process(self):
        scores = {}
        
        # 1. Publications
        pub_count = self._to_int(self.raw_answers.get('publications_count', 0))
        if pub_count > 0:
            scores['publications'] = min(15, pub_count * 3)
        else:
            has_pub = self._to_bool(self.raw_answers.get('has_publications', 'No'))
            scores['publications'] = 15 if has_pub else 0

        # 2. Citations
        citations = self._to_int(self.raw_answers.get('citations_count', 0))
        if citations >= 100:
            scores['citations'] = 15
        elif citations >= 50:
            scores['citations'] = 10
        elif citations >= 10:
            scores['citations'] = 5
        else:
            scores['citations'] = 0

        # 3. Awards
        scores['awards'] = 10 if self._to_bool(self.raw_answers.get('has_awards')) else 0
        
        # 4. Media
        scores['media'] = 10 if self._to_bool(self.raw_answers.get('has_media')) else 0
        
        # 5. Judging
        scores['judging'] = 10 if self._to_bool(self.raw_answers.get('has_judging')) else 0
        
        # 6. Leadership
        scores['leadership'] = 10 if self._to_bool(self.raw_answers.get('has_leadership')) else 0
        
        # 7. Salary
        scores['salary'] = 10 if self._to_bool(self.raw_answers.get('has_high_salary')) else 0
        
        # 8. Memberships
        scores['memberships'] = 5 if self._to_bool(self.raw_answers.get('has_memberships')) else 0
        
        # 9. Recommendations
        scores['recommendations'] = 10 if self._to_bool(self.raw_answers.get('can_get_letters')) else 0
        
        # 10. Endeavor
        endeavor_text = self.raw_answers.get('proposed_endeavor', '').strip()
        scores['endeavor'] = 5 if len(endeavor_text) > 20 else 0

        total_score = sum(scores.values())

        # Band Computation
        if total_score >= 80:
            band = 'strong profile'
        elif total_score >= 60:
            band = 'promising profile'
        elif total_score >= 40:
            band = 'developing profile'
        else:
            band = 'weak profile'

        # Compute strongest/weakest categories
        percents = []
        for cat, score in scores.items():
            max_score = self.MAX_SCORES[cat]
            percent = (score / max_score) * 100 if max_score > 0 else 0
            percents.append({'category': cat, 'score': score, 'max_score': max_score, 'percent': percent})

        # Sort descending by percent
        percents_desc = sorted(percents, key=lambda x: (x['percent'], x['score']), reverse=True)
        strongest = percents_desc[:3]
        
        # Sort ascending by percent
        percents_asc = sorted(percents, key=lambda x: (x['percent'], x['score']))
        weakest = percents_asc[:3]

        return {
            'total_score': total_score,
            'max_total': sum(self.MAX_SCORES.values()),
            'readiness_band': band,
            'category_scores': scores,
            'category_max': self.MAX_SCORES,
            'strongest_categories': strongest,
            'weakest_categories': weakest,
        }

    def _to_int(self, value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
            
    def _to_bool(self, value):
        if not value: return False
        if str(value).lower() in ['yes', 'true', '1', 'y']:
            return True
        return False
