from typing import Annotated, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.constants import (ClassificationType, ProcessingStatus, TaxType, DocumentType)

Aliquota = Annotated[float, Field(ge=0, le=100, description="Alíquota em %")]
ValorNaoNegativo = Annotated[float, Field(ge=0)]

CodigoItem = Annotated[str, Field(max_length=50)]
DescricaoItem = Annotated[str, Field(max_length=500)]
QuantidadeItem = Annotated[float, Field(gt=0)]
NcmOpcional = Annotated[Optional[str], Field(max_length=10, description="NCM do produto")]

NumeroNF = Annotated[str, Field(max_length=9)]
SerieNF = Annotated[str, Field(max_length=3)]
CNPJ = Annotated[str, Field(max_length=14)]
CPF = Annotated[str, Field(max_length=11)]
CFOP = Annotated[str, Field(max_length=4)]
NATOP = Annotated[str, Field(max_length=100)]
SCT = Annotated[str, Field(max_length=3)]
MensagemErro = Annotated[Optional[str], Field(max_length=500)]

# =============================================================
class Imposto(BaseModel):
    """Modelo para impostos."""
    model_config = ConfigDict(from_attributes=True)
    
    tipo_imposto: TaxType = Field(..., description="Tipo do imposto")
    aliquota: Aliquota 
    valor_base: ValorNaoNegativo = Field(..., description="Base de cálculo")
    valor_imposto: ValorNaoNegativo = Field(..., description="Valor do imposto")

class ItemNota(BaseModel):
    """Modelo para itens da nota."""
    model_config = ConfigDict(from_attributes=True)
    
    codigo_item: CodigoItem
    descricao: DescricaoItem
    quantidade: QuantidadeItem
    valor_unitario: ValorNaoNegativo
    valor_total: ValorNaoNegativo
    tipo: ClassificationType = Field(..., description="Produto ou Serviço")
    ncm: NcmOpcional

class NotaFiscal(BaseModel):
    """Modelo principal de nota fiscal."""
    model_config = ConfigDict(from_attributes=True)

    numero_nf: NumeroNF
    serie: SerieNF
    tipo_nf: DocumentType = Field(...)

    data_emissao: datetime = Field(...)
    data_processamento: datetime = Field(default_factory=datetime.now) 
    classificacao: ClassificationType = Field(...)

    cfop: CFOP
    natop: NATOP
    sct: SCT

    valor_total: ValorNaoNegativo

    fornecedor_cnpj: CNPJ
    cliente_cpf: CPF

    status: ProcessingStatus = Field(default=ProcessingStatus.PENDENTE)
    mensagem_erro: MensagemErro
    itens: List[ItemNota] = Field(default_factory=list) 
    imp: List[Imposto] = Field(default_factory=list)

class NotaFiscalDB(NotaFiscal):
    """Modelo para banco de dados (com ID)."""
    id: Optional[int] = Field(None, description="ID auto-incremento")