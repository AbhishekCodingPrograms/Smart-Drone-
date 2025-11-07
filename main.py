"""
Smart Farming Drones - Main Launcher Script
===========================================

This is the main entry point for the Smart Farming Drones AI project.
It provides a command-line interface to run different components of the system.

Author: Smart Farming AI Team
Date: 2024
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartFarmingLauncher:
    """
    Main launcher for Smart Farming Drones project
    """
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.project_root, 'scripts')
        self.dashboard_dir = os.path.join(self.project_root, 'dashboard')
        
        logger.info("Smart Farming Drones Launcher initialized")
    
    def check_dependencies(self):
        """
        Check if all required dependencies are installed
        """
        logger.info("Checking dependencies...")
        # Map PyPI package names to their importable module names.
        # Some packages have different import names than their distribution names.
        import importlib
        import importlib.util

        required_packages = {
            'tensorflow': ['tensorflow'],
            'opencv-python': ['cv2'],          # import name is cv2
            'numpy': ['numpy'],
            'pandas': ['pandas'],
            'matplotlib': ['matplotlib'],
            'flask': ['flask'],
            'plotly': ['plotly'],
            'scikit-learn': ['sklearn'],      # import name is sklearn
            'pillow': ['PIL']                 # import name is PIL
        }

        missing_packages = []

        for pkg_name, import_names in required_packages.items():
            found = False
            for import_name in import_names:
                # prefer importlib.util.find_spec which doesn't raise
                try:
                    if importlib.util.find_spec(import_name) is not None:
                        logger.info(f"✓ {pkg_name}")
                        found = True
                        break
                except Exception:
                    # fallback to import_module
                    try:
                        importlib.import_module(import_name)
                        logger.info(f"✓ {pkg_name}")
                        found = True
                        break
                    except Exception:
                        continue

            if not found:
                missing_packages.append(pkg_name)
                logger.warning(f"✗ {pkg_name}")
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Please install missing packages using: pip install -r requirements.txt")
            return False
        
        logger.info("All dependencies are installed!")
        return True
    
    def setup_project(self):
        """
        Setup project directories and generate sample data
        """
        logger.info("Setting up project...")
        
        # Create necessary directories
        directories = [
            'model', 'data/sample_images', 'data/mock_data',
            'dashboard/templates', 'dashboard/static/css', 'dashboard/static/js'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        
        # Generate sample data
        try:
            from scripts.sample_data_generator import SampleDataGenerator
            generator = SampleDataGenerator()
            generator.generate_all_sample_data()
            logger.info("Sample data generated successfully!")
        except Exception as e:
            logger.error(f"Error generating sample data: {str(e)}")
            return False
        
        return True
    
    def train_model(self):
        """
        Train the crop health detection model
        """
        logger.info("Training crop health detection model...")
        
        try:
            script_path = os.path.join(self.scripts_dir, 'model_training.py')
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("Model training completed successfully!")
                return True
            else:
                logger.error(f"Model training failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def run_drone_simulation(self, duration: int = 60):
        """
        Run drone simulation
        """
        logger.info(f"Running drone simulation for {duration} seconds...")
        
        try:
            script_path = os.path.join(self.scripts_dir, 'drone_simulation.py')
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("Drone simulation completed successfully!")
                return True
            else:
                logger.error(f"Drone simulation failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error running drone simulation: {str(e)}")
            return False
    
    def run_dashboard(self):
        """
        Run the Flask dashboard
        """
        logger.info("Starting Flask dashboard...")
        
        try:
            script_path = os.path.join(self.dashboard_dir, 'app.py')
            subprocess.run([sys.executable, script_path], cwd=self.project_root)
        
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Error running dashboard: {str(e)}")
    
    def generate_report(self):
        """
        Generate AI report
        """
        logger.info("Generating AI report...")
        
        try:
            script_path = os.path.join(self.scripts_dir, 'ai_reporting.py')
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("AI report generated successfully!")
                return True
            else:
                logger.error(f"AI report generation failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error generating AI report: {str(e)}")
            return False
    
    def run_image_processing_demo(self):
        """
        Run image processing demonstration
        """
        logger.info("Running image processing demonstration...")
        
        try:
            script_path = os.path.join(self.scripts_dir, 'image_processing.py')
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("Image processing demonstration completed!")
                return True
            else:
                logger.error(f"Image processing demonstration failed: {result.stderr}")
                return False
        
        except Exception as e:
            logger.error(f"Error running image processing demo: {str(e)}")
            return False
    
    def show_project_status(self):
        """
        Show project status and available files
        """
        logger.info("Project Status:")
        
        # Check main components
        components = {
            'Model Training Script': 'scripts/model_training.py',
            'Image Processing Module': 'scripts/image_processing.py',
            'Drone Simulation': 'scripts/drone_simulation.py',
            'AI Reporting System': 'scripts/ai_reporting.py',
            'Sample Data Generator': 'scripts/sample_data_generator.py',
            'Flask Dashboard': 'dashboard/app.py',
            'Dashboard Template': 'dashboard/templates/dashboard.html',
            'Requirements File': 'requirements.txt',
            'README': 'README.md'
        }
        
        for component, path in components.items():
            if os.path.exists(path):
                logger.info(f"✓ {component}: {path}")
            else:
                logger.warning(f"✗ {component}: {path} (missing)")
        
        # Check data files
        data_files = []
        if os.path.exists('data'):
            for root, dirs, files in os.walk('data'):
                for file in files:
                    data_files.append(os.path.join(root, file))
        
        if data_files:
            logger.info(f"Data files ({len(data_files)}):")
            for file in data_files[:10]:  # Show first 10 files
                logger.info(f"  - {file}")
            if len(data_files) > 10:
                logger.info(f"  ... and {len(data_files) - 10} more files")
        else:
            logger.warning("No data files found. Run 'python main.py setup' to generate sample data.")

def main():
    """
    Main function with command-line interface
    """
    parser = argparse.ArgumentParser(
        description='Smart Farming Drones - AI-Powered AgriTech Innovation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py setup                    # Setup project and generate sample data
  python main.py train                     # Train the AI model
  python main.py simulate                  # Run drone simulation
  python main.py dashboard                 # Start web dashboard
  python main.py report                    # Generate AI report
  python main.py demo                      # Run image processing demo
  python main.py status                    # Show project status
  python main.py all                       # Run complete workflow
        """
    )
    
    parser.add_argument('command', choices=[
        'setup', 'train', 'simulate', 'dashboard', 'report', 
        'demo', 'status', 'all', 'check'
    ], help='Command to execute')
    
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration for drone simulation (seconds)')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize launcher
    launcher = SmartFarmingLauncher()
    
    print("\n" + "="*60)
    # Avoid Unicode console issues on Windows by stripping non-ASCII
    banner = "SMART FARMING DRONES - AI-POWERED AGRI-TECH INNOVATION"
    try:
        print(banner)
    except UnicodeEncodeError:
        print(banner.encode('ascii', errors='ignore').decode('ascii'))
    print("="*60)
    print(f"Command: {args.command}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        if args.command == 'check':
            success = launcher.check_dependencies()
            sys.exit(0 if success else 1)
        
        elif args.command == 'setup':
            success = launcher.setup_project()
            sys.exit(0 if success else 1)
        
        elif args.command == 'train':
            if not launcher.check_dependencies():
                sys.exit(1)
            success = launcher.train_model()
            sys.exit(0 if success else 1)
        
        elif args.command == 'simulate':
            if not launcher.check_dependencies():
                sys.exit(1)
            success = launcher.run_drone_simulation(args.duration)
            sys.exit(0 if success else 1)
        
        elif args.command == 'dashboard':
            # Allow dashboard to run even if heavy ML packages are missing
            try:
                launcher.run_dashboard()
            except Exception as e:
                logger.error(f"Dashboard failed to start: {e}")
                sys.exit(1)
        
        elif args.command == 'report':
            if not launcher.check_dependencies():
                sys.exit(1)
            success = launcher.generate_report()
            sys.exit(0 if success else 1)
        
        elif args.command == 'demo':
            if not launcher.check_dependencies():
                sys.exit(1)
            success = launcher.run_image_processing_demo()
            sys.exit(0 if success else 1)
        
        elif args.command == 'status':
            launcher.show_project_status()
        
        elif args.command == 'all':
            logger.info("Running complete workflow...")
            
            # Check dependencies
            if not launcher.check_dependencies():
                sys.exit(1)
            
            # Setup project
            if not launcher.setup_project():
                sys.exit(1)
            
            # Train model
            if not launcher.train_model():
                sys.exit(1)
            
            # Run simulation
            if not launcher.run_drone_simulation(120):  # 2 minutes
                sys.exit(1)
            
            # Generate report
            if not launcher.generate_report():
                sys.exit(1)
            
            logger.info("Complete workflow finished successfully!")
            logger.info("You can now run 'python main.py dashboard' to start the web interface")
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
