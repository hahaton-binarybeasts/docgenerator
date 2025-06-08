from uuid import UUID
import requests
from typing import Optional, Dict, Any, Union
from app.schemas import Project
import json


class RestApiClient:
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL API
            headers: Заголовки по умолчанию
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if headers:
            self.session.headers.update(headers)
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        kwargs = {
            'params': params,
            'headers': headers
        }
        
        if data:
            if self.session.headers.get('Content-Type', '').startswith('application/json'):
                kwargs['json'] = data
            else:
                kwargs['data'] = data
        
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def _get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], list]:
        """GET запрос"""
        response = self._make_request('GET', endpoint, params=params, headers=headers)
        return response.json() if response.content else {}
    
    def _post(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], list]:
        """POST запрос"""
        response = self._make_request('POST', endpoint, data=data, params=params, headers=headers)
        return response.json() if response.content else {}
    
    def _put(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], list]:
        """PUT запрос"""
        response = self._make_request('PUT', endpoint, data=data, params=params, headers=headers)
        return response.json() if response.content else {}
    
    def _patch(
        self, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], list]:
        """PATCH запрос"""
        response = self._make_request('PATCH', endpoint, data=data, params=params, headers=headers)
        return response.json() if response.content else {}
    
    def _delete(
        self, 
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Union[Dict[str, Any], list]:
        """DELETE запрос"""
        response = self._make_request('DELETE', endpoint, params=params, headers=headers)
        return response.json() if response.content else {}

    def get_projects(self) -> list[Project]:
        projects_raw = self._get("projects")
        projects: list[Project] = []
        for p in projects_raw:
            projects.append(Project.model_validate(p))
        
        return projects
    
    def get_project(self, id: UUID) -> Project:
        project_raw = self._get(f"project/{id}")
        project = Project.model_validate(project_raw)

        return project
