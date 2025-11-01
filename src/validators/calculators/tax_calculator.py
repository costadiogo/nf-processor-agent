"""Calculadora de impostos para Produtos e Serviços."""

from typing import Optional

from src.constants import TaxType, ClassificationType
from logs.logger import app_logger


class TaxCalculator:
    """Calculadora de impostos para NFe e RPS."""
    
    # Alíquotas padrão para PRODUTOS
    ALIQUOTAS_PRODUTO = {
        TaxType.ICMS: 18.0,
        TaxType.IPI: 10.0,
        TaxType.PIS: 1.65,
        TaxType.COFINS: 7.6,
    }
    
    # Alíquotas padrão para SERVIÇOS
    ALIQUOTAS_SERVICO = {
        TaxType.ISS: 5.0,
        TaxType.PIS: 0.65,
        TaxType.COFINS: 3.0,
        TaxType.INSS: 11.0,
        TaxType.IRPJ: 1.5,
        TaxType.CSLL: 1.0,
    }
    
    def __init__(self, nf_data: dict):
        """Inicializa calculadora."""
        self.nf_data = nf_data
        self.valor_total = nf_data.get('valor_total', 0)
        self.classificacao = nf_data.get('classificacao', '')
        self.impostos_calculados = []
    
    def calcular_todos(self) -> list[dict]:
        """Calcula todos os impostos baseado na classificação."""
        self.impostos_calculados = []
        
        # Determinar se é produto ou serviço
        is_produto = self.classificacao in [
            ClassificationType.PRODUTO.value,
            ClassificationType.AMBOS.value
        ]
        
        is_servico = self.classificacao in [
            ClassificationType.SERVICO.value,
            ClassificationType.AMBOS.value
        ]
        
        # Impostos de PRODUTO
        if is_produto:
            self._calcular_icms()
            self._calcular_ipi()
        
        # Impostos de SERVIÇO
        if is_servico:
            self._calcular_iss()
            self._calcular_inss()
            self._calcular_irpj()
            self._calcular_csll()
        
        # Impostos COMUNS (PIS/COFINS)
        self._calcular_pis(is_produto)
        self._calcular_cofins(is_produto)
        
        app_logger.info(f"✅ {len(self.impostos_calculados)} impostos calculados")
        return self.impostos_calculados
    
    # =====================================================
    # IMPOSTOS DE PRODUTO
    # =====================================================
    
    def _calcular_icms(self):
        """Calcula ICMS (Imposto sobre Circulação de Mercadorias)."""
        aliquota = self.ALIQUOTAS_PRODUTO[TaxType.ICMS]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.ICMS.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    def _calcular_ipi(self):
        """Calcula IPI (Imposto sobre Produtos Industrializados)."""
        aliquota = self.ALIQUOTAS_PRODUTO[TaxType.IPI]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.IPI.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    # =====================================================
    # IMPOSTOS DE SERVIÇO
    # =====================================================
    
    def _calcular_iss(self):
        """Calcula ISS (Imposto sobre Serviços)."""
        aliquota = self.ALIQUOTAS_SERVICO[TaxType.ISS]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.ISS.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    def _calcular_inss(self):
        """Calcula INSS (para serviços)."""
        aliquota = self.ALIQUOTAS_SERVICO[TaxType.INSS]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.INSS.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    def _calcular_irpj(self):
        """Calcula IRPJ (Imposto de Renda Pessoa Jurídica)."""
        aliquota = self.ALIQUOTAS_SERVICO[TaxType.IRPJ]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.IRPJ.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    def _calcular_csll(self):
        """Calcula CSLL (Contribuição Social sobre o Lucro)."""
        aliquota = self.ALIQUOTAS_SERVICO[TaxType.CSLL]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.CSLL.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    # =====================================================
    # IMPOSTOS COMUNS (PIS/COFINS)
    # =====================================================
    
    def _calcular_pis(self, is_produto: bool = True):
        """Calcula PIS."""
        # Alíquota diferente para produto vs serviço
        aliquota = self.ALIQUOTAS_PRODUTO[TaxType.PIS] if is_produto else self.ALIQUOTAS_SERVICO[TaxType.PIS]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.PIS.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    def _calcular_cofins(self, is_produto: bool = True):
        """Calcula COFINS."""
        # Alíquota diferente para produto vs serviço
        aliquota = self.ALIQUOTAS_PRODUTO[TaxType.COFINS] if is_produto else self.ALIQUOTAS_SERVICO[TaxType.COFINS]
        valor_base = self.valor_total
        valor_imposto = valor_base * (aliquota / 100)
        
        self.impostos_calculados.append({
            'tipo_imposto': TaxType.COFINS.value,
            'aliquota': aliquota,
            'valor_base': valor_base,
            'valor_imposto': round(valor_imposto, 2),
        })
    
    # =====================================================
    # MÉTODOS AUXILIARES
    # =====================================================
    
    def get_total_impostos(self) -> float:
        """Retorna total de impostos."""
        return sum(imp['valor_imposto'] for imp in self.impostos_calculados)
    
    def get_carga_tributaria_percentual(self) -> float:
        """Retorna carga tributária em %."""
        if self.valor_total == 0:
            return 0.0
        return (self.get_total_impostos() / self.valor_total) * 100
    
    def get_impostos_por_tipo(self) -> dict[str, float]:
        """Retorna dicionário com impostos por tipo."""
        impostos_dict = {}
        for imp in self.impostos_calculados:
            impostos_dict[imp['tipo_imposto']] = imp['valor_imposto']
        return impostos_dict


def calcular_impostos(nf_data: dict) -> list[dict]:
    """Função auxiliar para calcular impostos."""
    calc = TaxCalculator(nf_data)
    return calc.calcular_todos()
