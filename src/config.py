from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

RECENT_DATA_PATH = DATA_DIR / "recent_observations.csv"

AIRKOREA_SERVICE_KEY = os.getenv("AIRKOREA_SERVICE_KEY")
KMA_SERVICE_KEY = os.getenv("KMA_SERVICE_KEY")

AIRKOREA_URL = (
    "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/"
    "getMsrstnAcctoRltmMesureDnsty"
)

KMA_ULTRA_NCST_URL = (
    "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/"
    "getUltraSrtNcst"
)

ONSET_MODEL_PATH = MODEL_DIR / "best_model_onset_time_60_40.joblib"
PERSISTENCE_MODEL_PATH = MODEL_DIR / "best_model_persistence_time_60_40.joblib"

ONSET_FEATURES_PATH = MODEL_DIR / "selected_features_onset.json"
PERSISTENCE_FEATURES_PATH = MODEL_DIR / "selected_features_persistence.json"

ONSET_THRESHOLD_PATH = MODEL_DIR / "threshold_onset.json"
PERSISTENCE_THRESHOLD_PATH = MODEL_DIR / "threshold_persistence.json"