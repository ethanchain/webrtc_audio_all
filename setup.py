from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent

setup(
    name="webrtc_audio_all",
    version="0.1.0",
    description="WebRTC AudioProcessing (M110) packaged APM DLL + Python ctypes wrapper (AEC/NS/AGC/VAD)",
    packages=find_packages(),
    package_data={
        "webrtc_audio_all": ["bin/*.dll"]
    },
    include_package_data=True,
    python_requires=">=3.10",
)
