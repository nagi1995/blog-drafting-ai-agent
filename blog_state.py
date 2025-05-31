from typing import TypedDict, List, Dict, Any

class BlogState(TypedDict):
    code: str                                 
    section_drafts: Dict[str, str]            
    completed_sections: List[str]             
    skipped_sections: List[str]

    code_summary: str            
    sections: List[Dict[str, str]]  
    current_section: str            
    feedback: Dict[str, Any]
    target_section_no: str