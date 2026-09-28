import asyncio, json, traceback, sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient
path=Path('TON_IoT_Research_Benchmark.ipynb')
nb=nbformat.read(path,as_version=4)
client=NotebookClient(nb,timeout=3600,kernel_name='ton_iot_research',resources={'metadata':{'path':str(Path.cwd())}},allow_errors=False)
async def main():
    await client.async_setup_kernel()
    try:
        for i,cell in enumerate(nb.cells):
            if cell.cell_type=='code':
                print(f'RUNNING CELL {i+1}: {cell.source.splitlines()[0][:110]}',flush=True)
                await client.async_execute_cell(cell,i)
                nbformat.write(nb,path)
                errors=[o for o in cell.get('outputs',[]) if o.output_type=='error']
                if errors: print('CELL ERROR SAVED',errors[0].get('ename'),flush=True)
            else:
                nbformat.write(nb,path)
    except BaseException:
        nbformat.write(nb,path)
        traceback.print_exc()
        raise
    finally:
        await client.async_cleanup_kernel()
    print('NOTEBOOK EXECUTION COMPLETE',flush=True)
asyncio.run(main())

