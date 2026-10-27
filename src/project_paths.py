from pathlib import Path
import os
WORKDIR=Path(os.environ.get('APMCM_WORKDIR',Path(__file__).resolve().parents[1]/'.runtime')).resolve()
if not (WORKDIR/'.apmcm-workspace').is_file():
    raise RuntimeError('Initialize an isolated demo workspace with python scripts/create_demo.py before running archived analysis scripts. Do not point at an original project directory.')

def require_historical_templates():
    """Historical paper/submission templates contain unverified narrative and old fixed metrics."""
    if os.environ.get('APMCM_ALLOW_HISTORICAL_TEMPLATES')!='1':
        raise RuntimeError('Historical unverified paper/submission template disabled. It is not a record of participation, results or actual AI interactions. Read SCRIPT_STATUS.md before explicitly enabling it.')
