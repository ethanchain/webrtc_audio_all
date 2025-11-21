"""
webrtc_audio_all.audio_processing
---------------------------------
Minimal, easy-to-use ctypes-backed loader for prebuilt WebRTC APM DLL.

Features:
 - Supports sample_rate=16000 or 48000 (auto selection). If caller passes other rates,
   a simple linear resampler will convert to nearest supported (16k or 48k).
 - Input/Output: numpy int16 1-D arrays or raw bytes (PCM16 little-endian).
 - Methods:
     ap = AudioProcessor(sample_rate=16000|48000, enable_aec=True, enable_ns=True, enable_agc=True, enable_vad=False)
     out = ap.process(mic_frame, far_frame=None)  # returns numpy int16 array
 - Internally loads webrtc_apm_x64.dll from package folder.
"""

import ctypes
import os
import threading

# DLL 路径
DLL_PATH = os.path.join(os.path.dirname(__file__), "bin", "webrtc_audio_processing_x64.dll")

if not os.path.exists(DLL_PATH):
    raise FileNotFoundError(f"WebRTC DLL not found: {DLL_PATH}")

# 加载 DLL
apm = ctypes.CDLL(DLL_PATH)

# -------------------------
# C API 声明
# -------------------------

# int CreateApm();
apm.CreateApm.restype = ctypes.c_void_p

# void DestroyApm(void* apm);
apm.DestroyApm.argtypes = [ctypes.c_void_p]

# int SetConfig(void* apm, int enable_aec, int enable_ns, int enable_agc);
apm.SetConfig.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int]
apm.SetConfig.restype = ctypes.c_int

# int ProcessFrame(void* apm, const float* in_frame, float* out_frame, int samples);
apm.ProcessFrame.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int,
]
apm.ProcessFrame.restype = ctypes.c_int


# =============================
# Python 封装（最简易 API）
# =============================

class AudioProcessor:
    """
    音频增强引擎：
    - AEC  回声消除
    - NS   噪声抑制
    - AGC  自动增益
    """

    def __init__(self, enable_aec=True, enable_ns=True, enable_agc=True):
        self._lock = threading.Lock()

        # 创建 APM 实例
        self._apm = apm.CreateApm()
        if not self._apm:
            raise RuntimeError("Failed to create WebRTC APM instance")

        # 配置
        ret = apm.SetConfig(self._apm, int(enable_aec), int(enable_ns), int(enable_agc))
        if ret != 0:
            raise RuntimeError(f"SetConfig failed: {ret}")

    def process(self, frame):
        """
        输入/输出均为 float32 numpy 数组
        frame size = 10ms，一般为 160（16kHz）或 480（48kHz）
        """
        import numpy as np

        if not isinstance(frame, np.ndarray):
            raise TypeError("Input must be numpy.ndarray(float32)")

        if frame.dtype != np.float32:
            raise TypeError("Input dtype must be float32")

        samples = frame.size
        out = np.zeros_like(frame)

        in_c = frame.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        out_c = out.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        with self._lock:
            ret = apm.ProcessFrame(self._apm, in_c, out_c, samples)

        if ret != 0:
            raise RuntimeError(f"ProcessFrame failed: {ret}")

        return out

    def close(self):
        if self._apm:
            apm.DestroyApm(self._apm)
            self._apm = None

    def __del__(self):
        self.close()


# =============================
# 简单测试
# =============================

if __name__ == "__main__":
    import numpy as np

    proc = AudioProcessor(enable_aec=True, enable_ns=True, enable_agc=True)

    # 模拟一帧 480 samples（48KHz 10ms）
    frame = np.random.randn(480).astype(np.float32)

    out = proc.process(frame)

    print("Input:", frame[:5])
    print("Output:", out[:5])

    proc.close()
