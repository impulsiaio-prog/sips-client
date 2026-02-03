#!/usr/bin/env python3
"""
Ejemplo de uso del SIPS Client
"""

from sips_client import SIPSClient

def main():
    """Ejemplo básico de uso"""
    
    # Crear cliente (usa variables de entorno del .env)
    client = SIPSClient()
    
    # Ejemplo 1: Consultar CUPS sin guardar en CouchDB
    print("\n" + "="*60)
    print("EJEMPLO 1: Consulta sin guardar en CouchDB")
    print("="*60)
    
    cups_ejemplo = "ES0031406091590001JF0F"
    sips_data = client.get_sips_history(
        cups=cups_ejemplo,
        months=6,
        save_to_couch=False  # No guardar
    )
    
    if sips_data:
        print(f"\n✅ Datos obtenidos:")
        print(f"   - CUPS: {sips_data['cups']}")
        print(f"   - Registros: {sips_data['records_found']}")
        print(f"   - Periodos: {', '.join(sips_data['periods'])}")
        print(f"   - Potencias actuales: {sips_data['current_powers']}")
    
    # Ejemplo 2: Consultar y guardar en CouchDB
    print("\n" + "="*60)
    print("EJEMPLO 2: Consulta y guardado en CouchDB")
    print("="*60)
    
    sips_data = client.get_sips_history(
        cups=cups_ejemplo,
        invoice_id=12345,
        months=12,
        save_to_couch=True  # Guardar automáticamente
    )
    
    if sips_data:
        print(f"\n✅ Datos guardados en CouchDB")
    
    # Ejemplo 3: Múltiples CUPS
    print("\n" + "="*60)
    print("EJEMPLO 3: Procesamiento de múltiples CUPS")
    print("="*60)
    
    cups_list = [
        "ES0031406091590001JF0F",
        "ES0021000000000000AA",
        "ES0022000000000000BB",
    ]
    
    for cups in cups_list:
        print(f"\nProcesando: {cups}")
        data = client.get_sips_history(
            cups=cups,
            months=3,
            save_to_couch=True
        )
        if data:
            print(f"   ✅ {data['records_found']} registros encontrados")
        else:
            print(f"   ⚠️  No se encontraron datos")
    
    # Cerrar conexión
    client.disconnect_db()
    
    print("\n" + "="*60)
    print("✅ EJEMPLOS COMPLETADOS")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
