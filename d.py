import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from typing import List
import xnoapi
from xnoapi.vn.data.stocks import Quote 

API_KEY = "izIj0Y6dXKvCWhLaZDWa8mnhIycWVL6pa2yISIV0ZobYtdHk1uaj9uaY1aabM3vZZuzIkcU4qGpWijDlcDLnWFklLNMaJIvvRJhieWaInILJZZBcGEhvM9LkLNZIzSTi" 

try:
    xnoapi.client(apikey=API_KEY)
    print("Khởi tạo XNO API Client thành công.")
except Exception as e:
    print(f"Lỗi khởi tạo XNO API: {e}. Vui lòng kiểm tra API Key.")
   
warnings.simplefilter(action='ignore', category=FutureWarning)
sns.set_theme(style="whitegrid")

START_DATE = '2024-11-07'
END_DATE = '2025-11-10'
SINGLE_SYMBOL = "VCB.VN"
COMPARISON_TICKERS = ["VCB.VN", "MBB.VN", "ACB.VN", "CTG.VN", "BID.VN"]
VOLUME_THRESHOLD = 1_000_000
API_INTERVAL = '1D' 

def analyze_single_stock(symbol_full: str, start: str, end: str):
    """
    Tải (từ XNO API), xử lý, vẽ biểu đồ và lọc cho một mã cổ phiếu duy nhất.
    """
    symbol = symbol_full.replace(".VN", "")
    print(f"\n--- PHÂN TÍCH MÃ ĐƠN: {symbol_full} (XNO API) ---")
    
    try:
        print(f"Đang tải dữ liệu lịch sử cho: {symbol}...")
        q = Quote(symbol)
        df = q.history(start=start, end=end, interval=API_INTERVAL)

        if df is None or df.empty:
            print(f"Dữ liệu {symbol} tải về bị rỗng.")
            return
        print(f"Tải dữ liệu {symbol} thành công.")

       
        df['time'] = pd.to_datetime(df.index)
        
    except Exception as e:
        print(f"Lỗi khi tải hoặc xử lý dữ liệu {symbol}: {e}")
        return 
    
    
    clean_symbol = symbol 
    print(f"Vẽ biểu đồ giá {clean_symbol}...")
    plt.figure(figsize=(10, 5))
    plt.plot(df['time'], df['close'], color='royalblue', label='Giá đóng cửa')
    plt.xticks(rotation=45)
    plt.title(f'GIÁ ĐÓNG CỬA {symbol_full}\n({start} đến {end})')
    plt.xlabel('Thời gian')
    plt.ylabel('Giá đóng cửa (VND)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"bieu_do_{clean_symbol}.png")
    print(f"Đã lưu bieu_do_{clean_symbol}.png")
    print(f"\nLọc các ngày {symbol_full} có volume > {VOLUME_THRESHOLD:,}...")
   
    df_filtered = df[df["volume"] > VOLUME_THRESHOLD].copy()

    if not df_filtered.empty:
        print(f"Tìm thấy {len(df_filtered)} phiên:")
        
        print(df_filtered[['time', 'close', 'volume']].tail())
    else:
        print(f"Không có phiên nào của {symbol_full} có volume > {VOLUME_THRESHOLD:,}.")

def analyze_comparison(tickers: List[str], start: str, end: str):
    """
    Tải (từ XNO API) và vẽ biểu đồ so sánh cho nhiều mã cổ phiếu.
    """
    print("\n--- PHÂN TÍCH SO SÁNH NHÓM NGÂN HÀNG (XNO API) ---")
    
    df_closes_list = []
    
  
    for ticker_full in tickers:
        ticker = ticker_full.replace(".VN", "")
        print(f"  > Đang tải {ticker}...")
        
        try:
            q = Quote(ticker)
            df = q.history(start=start, end=end, interval=API_INTERVAL)
            
            if df is not None and not df.empty:
                df_close = df[['close']].rename(columns={'close': ticker_full})
                df_close.index = pd.to_datetime(df_close.index) 
                df_closes_list.append(df_close)
            else:
                print(f"  > Không có dữ liệu cho {ticker}.")
                
        except KeyError: 
             print(f"  > Lỗi: Không tìm thấy cột 'close' trong dữ liệu của {ticker}.")
        except Exception as e:
            print(f"  > Lỗi tải {ticker}: {e}")
            
    if not df_closes_list:
        print("Không có dữ liệu để so sánh.")
        return

    df_closes = pd.concat(df_closes_list, axis=1, join='inner')
    df_closes.columns.name = 'Ticker' 
    
    if df_closes.empty:
        print("Dữ liệu sau khi ghép (join) bị rỗng.")
        return
        
    print("Tải và ghép dữ liệu so sánh thành công.")
    
    
    df_long_base = df_closes.copy()
    df_long_base['time'] = pd.to_datetime(df_long_base.index)
    
    # Melt trên cột 'time' an toàn
    data_long = df_long_base.melt('time', var_name='Ticker', value_name='close')
    
    data_long['Ticker'] = data_long['Ticker'].str.replace(".VN", "")

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=data_long, x="time", y="close", hue="Ticker")
    plt.title(f"So sánh giá cổ phiếu ngân hàng\n({start} đến {end})")
    plt.xlabel("Thời gian")
    plt.ylabel("Giá đóng cửa (VND)")
    plt.savefig("bieu_do_so_sanh_gia.png")
    print("Đã lưu bieu_do_so_sanh_gia.png")
   
    df_closes_perf = df_closes.dropna() 
    if df_closes_perf.empty:
        print("Không đủ dữ liệu (sau khi lọc NaN) để tính tăng trưởng.")
        return
        
    perf = (df_closes_perf.iloc[-1] / df_closes_perf.iloc[0] - 1) * 100
    perf_df = perf.reset_index()
    perf_df.columns = ['Ticker', 'Tăng trưởng (%)']
    perf_df['Ticker'] = perf_df['Ticker'].str.replace(".VN", "")
    
    plt.figure(figsize=(10, 5))
    sns.barplot(data=perf_df, x="Ticker", y="Tăng trưởng (%)", palette="crest")
    plt.title(f"Hiệu suất tăng trưởng cổ phiếu ngân hàng\n({start} đến {end})")
    plt.savefig("bieu_do_tang_truong.png")
    print("Đã lưu bieu_do_tang_truong.png")
    
    print("\nBẢNG TĂNG TRƯỞNG (%):")
    print(perf_df.sort_values(by='Tăng trưởng (%)', ascending=False).to_string(index=False))

def main():
    """Hàm chính điều phối các tác vụ."""
    
    analyze_single_stock(SINGLE_SYMBOL, START_DATE, END_DATE)
    analyze_comparison(COMPARISON_TICKERS, START_DATE, END_DATE)
    print("\n--- HOÀN TẤT TẤT CẢ PHÂN TÍCH ---")
    plt.show() 
    input("\n=== TẤT CẢ BIỂU ĐỒ ĐÃ HIỆN. NHẤN ENTER ĐỂ ĐÓNG. ===")

if __name__ == "__main__":
    main()