from models import LinearBackground, GaussianPeak, KuboSakaiBoronPeak

default_prefs = {
    "peak_type" : "gaussian",
    "boron_peak_type" : "kubo_sakai",
    "background_type" : "linear",
    "overlap_rois" : True,
    "roi_width" : 15,
    "B_roi_width" : 20
}
som = {
    "backgrounds":
    {
        "linear":LinearBackground
    },
    "peaks":
    {
        "gaussian":GaussianPeak,
        "kubo_sakai":KuboSakaiBoronPeak
    }
}