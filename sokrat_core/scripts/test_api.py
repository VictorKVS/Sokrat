import requests
import sys
import json

def test_query(query):
    """Тестируем API запросом"""
    
    url = "http://localhost:8000/analyze"
    payload = {"query": query}
    
    print(f"\n Тестовый запрос: {query}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        print(f" Query ID: {result['query_id']}")
        print(f" Источников: {len(result['sources'])}")
        
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source['title']}")
        
        print("\n Ответы моделей:")
        for model, analysis in result['model_analyses'].items():
            print(f"\n{model}:")
            print("-" * 40)
            # Показываем первые 500 символов
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
        
        if result['confidence_flags']:
            print("\n Флаги:")
            for flag in result['confidence_flags']:
                print(f"   {flag}")
                
    except requests.exceptions.ConnectionError:
        print(" Сервер не запущен! Запусти: uvicorn src.main:app --reload")
    except Exception as e:
        print(f" Ошибка: {e}")

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "волновая электростанция эффективность"
    test_query(query)
