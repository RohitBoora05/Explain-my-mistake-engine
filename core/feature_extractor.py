from typing import Dict , Any

# constant

CONFIDENCE_MAP = {
    "Low" : 0.2 ,
    "Medium": 0.5 ,
    "High" : 0.8
} 

DEFAULT_CONFIDENCE = 0.5
DEFAULT_ELIMINATION_RATIO = 0.25
DEAFAULT_TIME_PRESSURE = 0.5 
MAX_REVISION_NORMALIZER = 3

EXPECTED_COMPLETENESS_FIELDS = [
    "confidence_input" ,
    "elimination_options" ,
    "expected_time"
]

# clamping 

def clamp (value : float , min_value : float = 0.0 , max_value : float = 1.0) -> float:
    return max(min_value, min(value , max_value))

#public api 

def extract_features(attempt_data: Dict[str,Any]) -> Dict[str, float]:
    raw = _parse_inputs(attempt_data)

    time_taken = _build_time_taken(raw)
    confidence_level = _build_confidence_level(raw)
    elimination_ratio = _build_elimination_ratio(raw)
    revision_count = _build_revision_count(raw)

    time_pressure = _build_time_pressure(time_taken, raw)
    confidence_time_conflict = _build_confidence_time_conflict(confidence_level , time_taken)
    revision_after_confidence = _build_revision_after_confidence(confidence_level, revision_count)

    data_completeness = _build_data_completeness(raw)

    feature_vector = _assemble_feature_vector(
        time_taken ,
        confidence_level , 
        elimination_ratio ,
        revision_count ,
        data_completeness ,
        time_pressure ,
        confidence_time_conflict ,
        revision_after_confidence
    )

    _validation_feature_vector(feature_vector)

    return feature_vector

# input

def _parse_inputs(attempts_data: Dict[str, Any]) -> Dict[str,Any]:
    return{
        "start_time":attempts_data.get("start_time"),
        "submit_time":attempts_data.get("submit_time"),
        "revision_log":attempts_data.get("revision_log",2),
        "total_options":attempts_data.get("total_options",4),

        "confidence_input":attempts_data.get("confidence_input"),
        "elimination_options":attempts_data.get("elimination_options"),
        "expected_time": attempts_data.get("expected_data"),
    }

# features

def _build_time_taken(raw: Dict[str , Any]) -> float:
    start = raw["start_time"]
    submit = raw["submit_time"]

    if start is None or submit is None:
        raise ValueError("start_time and submit_time are required")
    
    if submit < start:
        raise ValueError("submit_time cannot be earlier than start_time")
    
    return float(submit - start)

def _build_confidence_level(raw: Dict[str, Any]) -> float:
    confidence = raw["confidence_input"]

    if confidence in CONFIDENCE_MAP: 
        return CONFIDENCE_MAP[confidence] 
    
    return DEFAULT_CONFIDENCE

def _build_elimination_ratio(raw: Dict[str,Any]) -> float:
    eliminated = raw["eliminated_options"]
    total = raw["total_options"]

    if eliminated is None or total is None or total <= 0 :
        return DEFAULT_ELIMINATION_RATIO
    
    ratio = eliminated / total 
    return clamp(ratio)

def _build_revision_count(raw :Dict[str, Any]) -> float:
    revisions = raw.get("revision_log",0)
    normalized = revisions / MAX_REVISION_NORMALIZER
    return clamp(normalized)

# derived 

def _build_time_pressure(time_taken: float , raw: Dict[str, Any])-> float:
    expected_time = raw["expected_time"]

    if expected_time is None or expected_time <=0 :
        return DEAFAULT_TIME_PRESSURE
    
    ratio = clamp(time_taken / expected_time)
    return 1.0 - ratio

def _build_confidence_time_conflict(confidence: float , time_pressure: float) -> float:
    return clamp(confidence * time_pressure)
def _build_revision_after_confidence(confidence: float , revision_count: float)-> float:
    return clamp(confidence * revision_count)

# data completeness 

def _build_data_completeness(raw: Dict[str ,Any]) -> float:
    provided = 0 

    for field in EXPECTED_COMPLETENESS_FIELDS:
        if raw.get(field) is not None:
            provided += 1

    return provided / len(EXPECTED_COMPLETENESS_FIELDS)

# validation and assembly 

def _assemble_feature_vector(
        time_taken: float,
        confidence_level: float,
        elimination_ratio: float,
        revision_count: float,
        data_completeness:float,
        time_pressure: float,
        confidence_time_conflict: float,
        revision_after_confidence: float
) -> Dict[str, float]:
    
    return{
        "time_taken": time_taken,
        "confidence_level" : confidence_level,
        "elimination_ratio" : elimination_ratio,
        "revision_count" : revision_count,
        "data_completeness" : data_completeness,
        "time_pressure" :time_pressure,
        "confidence_time_conflict" : confidence_time_conflict,
        "revision_after_confidence" : revision_after_confidence
    }

def _validation_feature_vector(vector: Dict[str, float]) -> None:
    if len(vector) != 8:
        raise ValueError("FeatireVector1 must contain exactly 8 features")
    
    for key , value in vector.items():
        if value is None:
            raise ValueError(f"feature '{key}' is None")
        
        if isinstance(value, float) and (value != value):
            raise ValueError(f"Feature '{key}' is NaN")
        
        if key != "time_taken":
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"feature '{key}' out of range [0,1]")