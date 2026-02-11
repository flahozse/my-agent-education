# Sistema de Gestión de Identificación de Estudiantes

## Resumen

Este documento describe el sistema mejorado de gestión de identificación de estudiantes implementado en el agente de educación. El sistema permite almacenar y reutilizar la identificación del estudiante (número de documento o correo electrónico) a lo largo de toda la conversación, evitando solicitudes repetidas y mejorando la experiencia del usuario.

## Componentes Principales

### 1. Session Manager (`sac_agent/session_manager.py`)

Módulo central que gestiona el almacenamiento de la información del estudiante a través de sesiones.

**Clase Principal:** `StudentSessionManager`

**Métodos:**
- `set_student_identifier(session_id, identifier, identifier_type)`: Almacena la identificación
- `get_student_identifier(session_id)`: Recupera la identificación almacenada
- `has_identifier(session_id)`: Verifica si existe una identificación
- `mark_verified(session_id)`: Marca la sesión como verificada
- `clear_session(session_id)`: Elimina los datos de la sesión

### 2. Herramientas de Identificación (`sac_agent/tools/student_identification.py`)

Herramientas expuestas al agente para gestionar la identificación del estudiante.

**Funciones:**

#### `set_student_identifier(tool_context, identifier)`
Almacena la identificación del estudiante en la sesión actual.

**Parámetros:**
- `tool_context`: Contexto de la herramienta ADK
- `identifier`: Número de documento o email del estudiante

**Retorna:** Mensaje de confirmación

**Ejemplo:**
```python
# Usuario dice: "Mi documento es 1234567890"
# El agente llama:
result = set_student_identifier(tool_context, "1234567890")
# Retorna: "He registrado tu identificación: 1234567890 (tipo: documento)..."
```

#### `check_has_student_identifier(tool_context)`
Verifica si existe una identificación almacenada.

**Retorna:** "yes" o "no"

**Ejemplo:**
```python
# El agente verifica antes de solicitar información:
has_id = check_has_student_identifier(tool_context)
if has_id == "no":
    # Solicitar identificación al usuario
```

#### `get_stored_student_identifier(tool_context)`
Obtiene la identificación almacenada con información adicional.

**Retorna:** Información de la identificación o mensaje de ausencia

#### `clear_student_identifier(tool_context)`
Elimina la identificación almacenada (útil para cambiar de estudiante).

**Retorna:** Mensaje de confirmación

### 3. Herramientas BigQuery Modificadas (`sac_agent/tools/bigquery_tools.py`)

Todas las herramientas de consulta BigQuery han sido modificadas para usar automáticamente la identificación almacenada en lugar de solicitarla en cada llamada.

**Funciones Modificadas:**
- `get_student_info(tool_context)`: Información general del estudiante
- `get_payment_status(tool_context)`: Historial de pagos
- `get_enrollment_status(tool_context)`: Estado de matrícula
- `get_academic_grades(tool_context)`: Calificaciones académicas

**Comportamiento:**
1. Recuperan la identificación de la sesión automáticamente
2. Si no hay identificación, retornan un mensaje pidiendo al usuario que proporcione su identificación
3. Ejecutan la consulta BigQuery con el identificador almacenado

## Flujo de Trabajo

### Escenario 1: Primera Interacción del Usuario

```
Usuario: "Quiero saber el estado de mis pagos"

┌─────────────────────────────────────────────┐
│ Agente verifica identificación              │
│ check_has_student_identifier()              │
│ Retorna: "no"                              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Agente solicita identificación              │
│ "Por favor, indícame tu número de documento │
│  o correo electrónico registrado"           │
└─────────────────────────────────────────────┘
                    ↓
Usuario: "Mi documento es 1234567890"
                    ↓
┌─────────────────────────────────────────────┐
│ Agente almacena identificación              │
│ set_student_identifier("1234567890")        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Agente consulta pagos                       │
│ get_payment_status()                        │
│ (usa identificación almacenada)             │
└─────────────────────────────────────────────┘
```

### Escenario 2: Consultas Subsecuentes

```
Usuario: "Ahora muéstrame mis calificaciones"

┌─────────────────────────────────────────────┐
│ Agente verifica identificación              │
│ check_has_student_identifier()              │
│ Retorna: "yes"                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Agente consulta calificaciones directamente│
│ get_academic_grades()                       │
│ (usa identificación almacenada)             │
└─────────────────────────────────────────────┘
```

### Escenario 3: Cambio de Estudiante

```
Usuario: "Quiero consultar información de otro estudiante"

┌─────────────────────────────────────────────┐
│ Agente limpia identificación anterior       │
│ clear_student_identifier()                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ Agente solicita nueva identificación        │
│ "He eliminado la identificación anterior.   │
│  Por favor proporciona el nuevo número de   │
│  documento o correo electrónico"            │
└─────────────────────────────────────────────┘
```

## Ventajas del Sistema

### 1. **Experiencia de Usuario Mejorada**
- El estudiante proporciona su identificación solo una vez
- Las consultas subsecuentes son instantáneas
- Conversación más natural y fluida

### 2. **Eficiencia Operacional**
- Reducción de mensajes repetitivos
- Menor fricción en el flujo de conversación
- Procesamiento más rápido de múltiples consultas

### 3. **Mantenibilidad del Código**
- Separación clara de responsabilidades
- Sistema de sesión centralizado
- Fácil extensión para nuevas herramientas

### 4. **Seguridad**
- Validación de identificadores
- Soporte para verificación adicional (campo `verified`)
- Fácil implementación de autenticación futura

## Configuración

No se requiere configuración adicional. El sistema funciona automáticamente con las herramientas existentes del agente.

### Variables de Entorno Requeridas (existentes)

```bash
BQ_PROJECT_ID=your-project-id
BQ_DATASET_ID=your-dataset-id
BQ_STUDENTS_TABLE=student_info
BQ_PAYMENTS_TABLE=payments
BQ_ENROLLMENT_TABLE=enrollment
BQ_GRADES_TABLE=grades
```

## Ejemplo de Uso Completo

```
Usuario: "Hola, quiero saber si mi último pago se registró"

Agente: "Claro, para ayudarte con eso, necesito verificar tu identidad.
         ¿Podrías proporcionarme tu número de documento o correo electrónico registrado?"

Usuario: "juan.perez@example.com"

Agente: "He registrado tu identificación: juan.perez@example.com (tipo: correo electrónico).
         Ahora puedo consultar tu información sin necesidad de que vuelvas a proporcionarla."

         [Consulta pagos en BigQuery]

         **Historial de Pagos:**
         | Fecha Pago | Concepto | Monto | Método | Estado | Fecha Vencimiento |
         |------------|----------|-------|--------|--------|-------------------|
         | 2026-02-01 | Matrícula | $500.00 | Transferencia | Pagado | 2026-02-05 |

Usuario: "Y mis calificaciones?"

Agente: [Consulta directamente sin pedir identificación]

        **Historial Académico:**
        | Período | Código | Curso | Créditos | Nota | Estado |
        |---------|--------|-------|----------|------|--------|
        | 2026-1 | MKT101 | Marketing Digital | 3 | 4.50 | Aprobado |

        **Promedio General:** 4.50
```

## Extensiones Futuras

### 1. **Autenticación Mejorada**
El campo `verified` en la sesión permite implementar:
- Códigos de verificación por email/SMS
- Autenticación de dos factores
- Tokens de sesión temporales

### 2. **Persistencia entre Sesiones**
Actualmente las sesiones son en memoria. Se podría extender a:
- Redis para persistencia distribuida
- Base de datos para historial de sesiones
- Caché con expiración configurable

### 3. **Auditoría y Logging**
- Registro de accesos a información del estudiante
- Compliance con regulaciones de privacidad
- Métricas de uso del sistema

## Archivos Modificados/Creados

### Nuevos Archivos:
- `sac_agent/session_manager.py`
- `sac_agent/tools/student_identification.py`
- `STUDENT_IDENTIFICATION.md` (este documento)

### Archivos Modificados:
- `sac_agent/agent.py` - Agregadas nuevas herramientas
- `sac_agent/tools/__init__.py` - Exportadas nuevas funciones
- `sac_agent/tools/bigquery_tools.py` - Modificadas para usar sesión
- `sac_agent/prompt.py` - Actualizado con nuevas instrucciones

## Testing

Para probar el sistema:

```bash
cd /Users/franciscojavier.lahoz/Sw/agents-ia/adk-starter-pack/my-agent-education
adk run .
```

**Casos de prueba recomendados:**

1. ✅ Solicitar información sin proporcionar identificación primero
2. ✅ Proporcionar identificación y hacer múltiples consultas
3. ✅ Intentar cambiar de estudiante usando clear_student_identifier
4. ✅ Proporcionar email vs número de documento
5. ✅ Verificar que las consultas BigQuery usen el identificador correcto

## Soporte

Para problemas o preguntas sobre este sistema, revisar:
- Logs del agente para debugging
- Variables de entorno de BigQuery
- Configuración del proyecto GCP
