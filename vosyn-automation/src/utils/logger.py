"""
Structured Logger
Provides consistent logging across the application
"""

import logging
import json
from datetime import datetime
from pathlib import Path


class StructuredLogger:
   
    
    def __init__(self, name: str = "vosyn-automation", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(exist_ok=True)
        
       
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
      
        if self.logger.handlers:
            return
        
        
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        
       
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
    
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_event(
        self, 
        event_type: str, 
        message: str,
        job_id: str = None,
        run_id: str = None,
        portal: str = None,
        **extra_data
    ):
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event_type,
            'message': message,
        }
        
        if job_id:
            log_entry['job_id'] = job_id
        if run_id:
            log_entry['run_id'] = run_id
        if portal:
            log_entry['portal'] = portal
        
       
        log_entry.update(extra_data)
        
       
        self.logger.info(json.dumps(log_entry))
    
    def info(self, message: str, **kwargs):
        
        self.log_event('info', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        
        self.log_event('error', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        
        self.log_event('warning', message, **kwargs)
    
    def job_started(self, job_id: str, title: str, portals: list):
        
        self.log_event(
            'job_started',
            f"Started processing job: {title}",
            job_id=job_id,
            title=title,
            portals=portals
        )
    
    def job_completed(self, job_id: str, status: str):
       
        self.log_event(
            'job_completed',
            f"Job completed with status: {status}",
            job_id=job_id,
            status=status
        )
    
    def portal_started(self, job_id: str, run_id: str, portal: str):
       
        self.log_event(
            'portal_started',
            f"Starting portal automation: {portal}",
            job_id=job_id,
            run_id=run_id,
            portal=portal
        )
    
    def portal_success(self, job_id: str, run_id: str, portal: str, confirmation_id: str):
       
        self.log_event(
            'portal_success',
            f"Successfully posted to {portal}",
            job_id=job_id,
            run_id=run_id,
            portal=portal,
            confirmation_id=confirmation_id
        )
    
    def portal_failed(self, job_id: str, run_id: str, portal: str, error: str):
        
        self.log_event(
            'portal_failed',
            f"Failed to post to {portal}: {error}",
            job_id=job_id,
            run_id=run_id,
            portal=portal,
            error=error
        )



logger = StructuredLogger()


#  TESTING CODE 

if __name__ == "__main__":
    
    print("=" * 60)
    print("Testing Structured Logger")
    print("=" * 60)
    print()
    
    
    print("Test 1: Basic logging")
    logger.info("System started")
    logger.warning("This is a warning")
    logger.error("This is an error")
    print()
    
    print("Test 2: Job logging")
    logger.job_started(
        job_id='JOB_TEST_001',
        title='Test Software Engineer',
        portals=['laurentian', 'sfu']
    )
    print()
    
    print("Test 3: Portal logging")
    logger.portal_started(
        job_id='JOB_TEST_001',
        run_id='RUN_TEST_001',
        portal='laurentian'
    )
    
    logger.portal_success(
        job_id='JOB_TEST_001',
        run_id='RUN_TEST_001',
        portal='laurentian',
        confirmation_id='LAU_12345'
    )
    print()
    
    logger.portal_failed(
        job_id='JOB_TEST_001',
        run_id='RUN_TEST_002',
        portal='sfu',
        error='Login credentials invalid'
    )
    print()
    
    logger.job_completed(
        job_id='JOB_TEST_001',
        status='PARTIAL_FAILED'
    )
    print()
    
    print("=" * 60)
    print(" Logger test complete!")
    print("=" * 60)
    print()
    print("Check logs/vosyn-automation_*.log for detailed JSON logs")