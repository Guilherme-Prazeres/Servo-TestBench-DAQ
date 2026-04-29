# 📊 DAQ — Bancada de Ensaio de Servo Motores

<!-- ![Status](https://img.shields.io/badge/Status-Funcional-1D9E75?style=flat-square) -->
![Versão](https://img.shields.io/badge/Vers%C3%A3o-v1.1.0-185FA5?style=flat-square)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-gray?style=flat-square)

## 📋 Visão Geral
Este sistema de aquisição de dados (DAQ) para a bancada de ensaio de servo motores. Ele permite medir, registrar e analisar torque, corrente e tensão dos servos em tempo real, integrando o hardware a uma interface gráfica desenvolvida em **PyQt6**.

---

## 💻 Software & Instalação

### 📦 Download e Execução (Stable)
Para baixar o executavel, acesse [BEST Software Download](https://github.com/Guilherme-Prazeres/Servo-TestBench-DAQ/releases/) e baixe a versão mais recente.

### 🛠️ Instalação para Desenvolvedores
Caso queira rodar o código fonte ou contribuir com o projeto:

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/Guilherme-Prazeres/Servo-TestBench-DAQ.git
   cd Servo-TestBench-DAQ

### Grandezas Medidas
| Grandeza | Sensor / Método | Faixa | Resolução |
| :--- | :--- | :--- | :--- |
| **Torque** | Célula de carga + HX711| [ 0 – 15 kgf.cm ] | [ ≈ 0.6 kgf.cm ] |
| **Corrente** | ACS712  | [ 0 – 30 A ] | [ ≈ 73.9 mA ] |
| **Tensão** | Divisor resistivo | [ 0 – 30 V ] | [ ≈ 28.8 mV ] |

---

## 🔧 Hardware & Especificações

### Componentes Principais
| Componente | Modelo / Referência | Qtd | Observação |
| :--- | :--- | :--- | :--- |
| **Microcontrolador** | Arduino [ Nano ] | 1 | Controlador principal |
| **Sensor de Torque** | Célula de carga + Módulo HX711 | 1 | Leitura diferencial amplificada |
| **Sensor de Corrente**| [ ACS712 30A ] | 1 | Medição de corrente do servo |
| **Fonte de Tensão** | [ Fonte de bancada ou Bateria] | 1 | Alimentação isolada para o servo |

---

## ⚡ Conexões & Pinagem

<!-- > ⚠️ **ATENÇÃO:** Verifique SEMPRE a polaridade antes de energizar. Conexões invertidas podem danificar permanentemente os servos, os sensores e o microcontrolador. -->

### Tabela de Pinagem
| Pino MCU | Sinal | Destino | 
| :--- | :--- | :--- | 
| `PD3` | PWM saída | Sinal do Servo | 
| `[ VCC ]` | VCC Servo | V+ Servo (Fonte Externa) | 
| `[ GND ]` | GND comum | GND Servo + GND Arduino |
| `PD6` | DT (Data) | Módulo HX711 | 
| `PD7` | SCK (Clock) | Módulo HX711 | 
| `A3` | Analog In | Sensor de Corrente | 
| `A0` | Analog In | Divisor de Tensão | 

> ⚠️ **ATENÇÃO:** O GND deve ser comum entre a fonte de tensão e o arduino e o servo.

