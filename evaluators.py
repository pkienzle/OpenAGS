from baseClasses import Evaluator
import math

class HBondAnalysis(Evaluator):
    def __init__(self, ROIs):
        self.HPeak = None
        self.AlPeak = None
        self.APeak = None
        for r in ROIs:
            if r.get_range()[0] < 511 and r.get_range()[1] > 511:
                pairs = r.get_peak_pairs()
                for p in pairs:
                    if p[1].get_ele() == "Annihilation":
                        self.APeak = p[0]
                        break
            
            if r.get_range()[0] < 1778 and r.get_range()[1] > 1778:
                pairs = r.get_peak_pairs()
                for p in pairs:
                    if p[1].get_ele() == "Al-28":
                        self.AlPeak = p[0]
                        break
            
            if r.get_range()[0] < 2224 and r.get_range()[1] > 2224:
                pairs = r.get_peak_pairs()
                for p in pairs:
                    if p[1].get_ele() == "H-2":
                        self.HPeak = p[0]
                        break

    @staticmethod
    def get_theorhetical_bounds(scaleCorrect, shiftCorrect):
        if scaleCorrect and shiftCorrect:
            pass
        elif shiftCorrect:
            return [444.33, 445.65]
        elif scaleCorrect:
            pass
        else:
            pass

    def get_headings(self):
        return ["Statistic of Interest","Value", "95% CI +/-", "Theorhetical Statistic (Free)", "Theorhetical Statistic (Rigid)", "Free within CI", "Rigid within CI"]
    
    def get_results(self, scaleCorrect, shiftCorrect):
        if scaleCorrect:
            a = self.APeak.get_ctr()
            aVar = self.APeak.get_variances()[0]
        if shiftCorrect:
            b = self.AlPeak.get_ctr()
            bVar = self.AlPeak.get_variances()[0]
        c = self.HPeak.get_ctr()
        cVar = self.HPeak.get_variances()[0]
        if scaleCorrect and shiftCorrect:
            statistic = "(E_H - E_Al)/(E_Al - E_A)"
            result = (c-b)/(b-a)
            variance = ((c-b)/(b-a)**2)**2 * aVar + (-(c-b)/(b-a)**2)**2 * bVar + (1/(b-a))**2 * cVar #sum of var(x) * (df/dx)**2 where f(a,b,c) = (c-b)/(b-a)
        elif shiftCorrect:
            statistic = "E_H - E_Al"
            result = c-b
            variance = bVar + cVar
        elif scaleCorrect:
            statistic = "E_H/E_A"
            result = c/a
            variance = (-c/a**2)**2 * aVar + (1/a)**2 * cVar
        else:
            statistic = "E_H"
            result = c
            variance = cVar
        bounds = HBondAnalysis.get_theorhetical_bounds(scaleCorrect,shiftCorrect)
        return [statistic, result, 2*math.sqrt(variance), bounds[0], bounds[1], bounds[0] > result - 2*math.sqrt(variance), bounds[1] < result + 2*math.sqrt(variance)]

class MassSensEval(Evaluator):               
    def __init__(self, ROIs):
        self.ROIs = ROIs
    def get_headings(self):
        output = self.ROIs[0].get_peak_pairs()[0][1].get_output()
        return ["Isotope", "Peak Centroid (keV)"] + [output, output + " St. Dev"]

    def get_results(self, isotope_list):
        results = []
        for r in self.ROIs:
            for p in r.get_peak_pairs():
                if p[1].get_ele() in isotope_list:
                    peak_results = p[1].get_results(p[0].get_area(), p[0].get_area_stdev())
                    results.append([p[1].get_ele(), p[0].get_ctr(), *peak_results])