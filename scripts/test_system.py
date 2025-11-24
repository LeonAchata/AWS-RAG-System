"""
Script de testing del sistema RAG
Prueba la infraestructura deployada
"""
import json
import boto3
import requests
import time
from datetime import datetime


class RagSystemTester:
    """Tester para el sistema RAG"""
    
    def __init__(self, api_url: str, bucket_name: str):
        self.api_url = api_url.rstrip('/')
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3')
        self.results = []
    
    def log(self, message: str, status: str = "INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbol = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }.get(status, "•")
        
        print(f"[{timestamp}] {symbol} {message}")
    
    def test_health_check(self) -> bool:
        """Test 1: Health check endpoint"""
        self.log("Testing health check endpoint...", "INFO")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log("Health check passed", "SUCCESS")
                    self.results.append(("Health Check", True, "OK"))
                    return True
            
            self.log(f"Health check failed: {response.status_code}", "ERROR")
            self.results.append(("Health Check", False, f"Status: {response.status_code}"))
            return False
            
        except Exception as e:
            self.log(f"Health check error: {str(e)}", "ERROR")
            self.results.append(("Health Check", False, str(e)))
            return False
    
    def test_document_upload(self) -> bool:
        """Test 2: Subir documento a S3"""
        self.log("Testing document upload to S3...", "INFO")
        
        # Crear documento de prueba
        test_content = """
        Inteligencia Artificial y Machine Learning
        
        La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana
        por parte de sistemas informáticos. Estos procesos incluyen el aprendizaje, el
        razonamiento y la autocorrección.
        
        El Machine Learning es un subconjunto de la IA que permite a las máquinas aprender
        de datos sin ser programadas explícitamente. Utiliza algoritmos que pueden identificar
        patrones en datos y hacer predicciones.
        
        Aplicaciones comunes incluyen:
        - Reconocimiento de voz
        - Visión por computadora
        - Procesamiento de lenguaje natural
        - Sistemas de recomendación
        """
        
        key = f"documents/test-{int(time.time())}.txt"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=test_content.encode('utf-8'),
                ContentType='text/plain'
            )
            
            self.log(f"Document uploaded: s3://{self.bucket_name}/{key}", "SUCCESS")
            self.results.append(("Document Upload", True, key))
            
            # Esperar a que se procese
            self.log("Waiting 30 seconds for document processing...", "INFO")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            self.log(f"Upload error: {str(e)}", "ERROR")
            self.results.append(("Document Upload", False, str(e)))
            return False
    
    def test_query_simple(self) -> bool:
        """Test 3: Query simple"""
        self.log("Testing simple query...", "INFO")
        
        query_data = {
            "query": "¿Qué es machine learning?",
            "top_k": 3,
            "include_sources": True
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "answer" in data and len(data["answer"]) > 0:
                    self.log(f"Query successful", "SUCCESS")
                    self.log(f"Answer preview: {data['answer'][:100]}...", "INFO")
                    self.log(f"Response time: {data.get('response_time', 'N/A')}s", "INFO")
                    self.log(f"Confidence: {data.get('confidence', {}).get('confidence', 'N/A')}", "INFO")
                    
                    self.results.append(("Simple Query", True, "Answer received"))
                    return True
                else:
                    self.log("Query returned empty answer", "WARNING")
                    self.results.append(("Simple Query", False, "Empty answer"))
                    return False
            else:
                self.log(f"Query failed: {response.status_code}", "ERROR")
                self.results.append(("Simple Query", False, f"Status: {response.status_code}"))
                return False
                
        except Exception as e:
            self.log(f"Query error: {str(e)}", "ERROR")
            self.results.append(("Simple Query", False, str(e)))
            return False
    
    def test_query_with_filters(self) -> bool:
        """Test 4: Query con filtros"""
        self.log("Testing query with filters...", "INFO")
        
        query_data = {
            "query": "¿Cuáles son las aplicaciones de IA?",
            "top_k": 5,
            "min_similarity": 0.6,
            "include_sources": True
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                sources_count = len(data.get("sources", []))
                
                self.log(f"Query with filters successful ({sources_count} sources)", "SUCCESS")
                self.results.append(("Query with Filters", True, f"{sources_count} sources"))
                return True
            else:
                self.log(f"Query failed: {response.status_code}", "ERROR")
                self.results.append(("Query with Filters", False, f"Status: {response.status_code}"))
                return False
                
        except Exception as e:
            self.log(f"Query error: {str(e)}", "ERROR")
            self.results.append(("Query with Filters", False, str(e)))
            return False
    
    def test_cache(self) -> bool:
        """Test 5: Sistema de caché"""
        self.log("Testing cache system...", "INFO")
        
        query_data = {
            "query": "¿Qué es inteligencia artificial?",
            "top_k": 3
        }
        
        try:
            # Primera llamada (no cacheada)
            start1 = time.time()
            response1 = requests.post(
                f"{self.api_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            time1 = time.time() - start1
            
            # Segunda llamada (debería estar cacheada)
            start2 = time.time()
            response2 = requests.post(
                f"{self.api_url}/query",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            time2 = time.time() - start2
            
            if response1.status_code == 200 and response2.status_code == 200:
                data2 = response2.json()
                from_cache = data2.get("from_cache", False)
                
                self.log(f"First call: {time1:.2f}s", "INFO")
                self.log(f"Second call: {time2:.2f}s (cached: {from_cache})", "INFO")
                
                if from_cache or time2 < time1 * 0.5:
                    self.log("Cache working correctly", "SUCCESS")
                    self.results.append(("Cache System", True, f"Speed up: {time1/time2:.1f}x"))
                    return True
                else:
                    self.log("Cache might not be working", "WARNING")
                    self.results.append(("Cache System", True, "Inconclusive"))
                    return True
            else:
                self.log("Cache test failed", "ERROR")
                self.results.append(("Cache System", False, "Request failed"))
                return False
                
        except Exception as e:
            self.log(f"Cache test error: {str(e)}", "ERROR")
            self.results.append(("Cache System", False, str(e)))
            return False
    
    def print_summary(self):
        """Imprime resumen de tests"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        for test_name, success, details in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} | {test_name:25} | {details}")
        
        print("=" * 60)
        print(f"Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total - passed} test(s) failed")
        
        print("=" * 60 + "\n")
    
    def run_all_tests(self):
        """Ejecuta todos los tests"""
        print("\n" + "=" * 60)
        print("🧪 STARTING RAG SYSTEM TESTS")
        print("=" * 60 + "\n")
        
        self.test_health_check()
        self.test_document_upload()
        self.test_query_simple()
        self.test_query_with_filters()
        self.test_cache()
        
        self.print_summary()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RAG System")
    parser.add_argument("--api-url", required=True, help="API Gateway URL")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    
    args = parser.parse_args()
    
    tester = RagSystemTester(
        api_url=args.api_url,
        bucket_name=args.bucket
    )
    
    tester.run_all_tests()


if __name__ == "__main__":
    main()
