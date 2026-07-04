"""
Dataset schema definitions for the feature importance drift analysis.
Defines the structure of the raw and processed datasets.
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class DataSource(Enum):
    """Enumeration of supported data sources."""
    UCI_ELECTRICITY = "uci_electricity_load_diagrams"
    CUSTOM_CSV = "custom_csv"


@dataclass
class DatasetSchema:
    """
    Schema definition for the input dataset.
    Matches the structure of the UCI Electricity Load Diagrams dataset.
    """
    source: DataSource
    target_column: str = "ML1_PE"
    feature_columns: Optional[List[str]] = None
    timestamp_column: str = "timestamp"
    window_size_days: int = 30
    expected_features: List[str] = None

    def __post_init__(self):
        if self.expected_features is None:
            # Standard features from UCI dataset excluding target and timestamp
            self.expected_features = [
                "MT0", "MT1", "MT2", "MT3", "MT4", "MT5", "MT6", "MT7",
                "MT8", "MT9", "MT10", "MT11", "MT12", "MT13", "MT14", "MT15",
                "MT16", "MT17", "MT18", "MT19", "MT20", "MT21", "MT22", "MT23",
                "MT24", "MT25", "MT26", "MT27", "MT28", "MT29", "MT30", "MT31",
                "MT32", "MT33", "MT34", "MT35", "MT36", "MT37", "MT38", "MT39",
                "MT40", "MT41", "MT42", "MT43", "MT44", "MT45", "MT46", "MT47",
                "MT48", "MT49", "MT50", "MT51", "MT52", "MT53", "MT54", "MT55",
                "MT56", "MT57", "MT58", "MT59", "MT60", "MT61", "MT62", "MT63",
                "MT64", "MT65", "MT66", "MT67", "MT68", "MT69", "MT70", "MT71",
                "MT72", "MT73", "MT74", "MT75", "MT76", "MT77", "MT78", "MT79",
                "MT80", "MT81", "MT82", "MT83", "MT84", "MT85", "MT86", "MT87",
                "MT88", "MT89", "MT90", "MT91", "MT92", "MT93", "MT94", "MT95",
                "MT96", "MT97", "MT98", "MT99", "MT100", "MT101", "MT102", "MT103",
                "MT104", "MT105", "MT106", "MT107", "MT108", "MT109", "MT110", "MT111",
                "MT112", "MT113", "MT114", "MT115", "MT116", "MT117", "MT118", "MT119",
                "MT120", "MT121", "MT122", "MT123", "MT124", "MT125", "MT126", "MT127",
                "MT128", "MT129", "MT130", "MT131", "MT132", "MT133", "MT134", "MT135",
                "MT136", "MT137", "MT138", "MT139", "MT140", "MT141", "MT142", "MT143",
                "MT144", "MT145", "MT146", "MT147", "MT148", "MT149", "MT150", "MT151",
                "MT152", "MT153", "MT154", "MT155", "MT156", "MT157", "MT158", "MT159",
                "MT160", "MT161", "MT162", "MT163", "MT164", "MT165", "MT166", "MT167",
                "MT168", "MT169", "MT170", "MT171", "MT172", "MT173", "MT174", "MT175",
                "MT176", "MT177", "MT178", "MT179", "MT180", "MT181", "MT182", "MT183",
                "MT184", "MT185", "MT186", "MT187", "MT188", "MT189", "MT190", "MT191",
                "MT192", "MT193", "MT194", "MT195", "MT196", "MT197", "MT198", "MT199",
                "MT200", "MT201", "MT202", "MT203", "MT204", "MT205", "MT206", "MT207",
                "MT208", "MT209", "MT210", "MT211", "MT212", "MT213", "MT214", "MT215",
                "MT216", "MT217", "MT218", "MT219", "MT220", "MT221", "MT222", "MT223",
                "MT224", "MT225", "MT226", "MT227", "MT228", "MT229", "MT230", "MT231",
                "MT232", "MT233", "MT234", "MT235", "MT236", "MT237", "MT238", "MT239",
                "MT240", "MT241", "MT242", "MT243", "MT244", "MT245", "MT246", "MT247",
                "MT248", "MT249", "MT250", "MT251", "MT252", "MT253", "MT254", "MT255",
                "MT256", "MT257", "MT258", "MT259", "MT260", "MT261", "MT262", "MT263",
                "MT264", "MT265", "MT266", "MT267", "MT268", "MT269", "MT270", "MT271",
                "MT272", "MT273", "MT274", "MT275", "MT276", "MT277", "MT278", "MT279",
                "MT280", "MT281", "MT282", "MT283", "MT284", "MT285", "MT286", "MT287",
                "MT288", "MT289", "MT290", "MT291", "MT292", "MT293", "MT294", "MT295",
                "MT296", "MT297", "MT298", "MT299", "MT300", "MT301", "MT302", "MT303",
                "MT304", "MT305", "MT306", "MT307", "MT308", "MT309", "MT310", "MT311",
                "MT312", "MT313", "MT314", "MT315", "MT316", "MT317", "MT318", "MT319",
                "MT320", "MT321", "MT322", "MT323", "MT324", "MT325", "MT326", "MT327",
                "MT328", "MT329", "MT330", "MT331", "MT332", "MT333", "MT334", "MT335",
                "MT336", "MT337", "MT338", "MT339", "MT340", "MT341", "MT342", "MT343",
                "MT344", "MT345", "MT346", "MT347", "MT348", "MT349", "MT350", "MT351",
                "MT352", "MT353", "MT354", "MT355", "MT356", "MT357", "MT358", "MT359",
                "MT360", "MT361", "MT362", "MT363", "MT364", "MT365", "MT366", "MT367",
                "MT368", "MT369", "MT370", "MT371", "MT372", "MT373", "MT374", "MT375",
                "MT376", "MT377", "MT378", "MT379", "MT380", "MT381", "MT382", "MT383",
                "MT384", "MT385", "MT386", "MT387", "MT388", "MT389", "MT390", "MT391",
                "MT392", "MT393", "MT394", "MT395", "MT396", "MT397", "MT398", "MT399",
                "MT400", "MT401", "MT402", "MT403", "MT404", "MT405", "MT406", "MT407",
                "MT408", "MT409", "MT410", "MT411", "MT412", "MT413", "MT414", "MT415",
                "MT416", "MT417", "MT418", "MT419", "MT420", "MT421", "MT422", "MT423",
                "MT424", "MT425", "MT426", "MT427", "MT428", "MT429", "MT430", "MT431",
                "MT432", "MT433", "MT434", "MT435", "MT436", "MT437", "MT438", "MT439",
                "MT440", "MT441", "MT442", "MT443", "MT444", "MT445", "MT446", "MT447",
                "MT448", "MT449", "MT450", "MT451", "MT452", "MT453", "MT454", "MT455",
                "MT456", "MT457", "MT458", "MT459", "MT460", "MT461", "MT462", "MT463",
                "MT464", "MT465", "MT466", "MT467", "MT468", "MT469", "MT470", "MT471",
                "MT472", "MT473", "MT474", "MT475", "MT476", "MT477", "MT478", "MT479",
                "MT480", "MT481", "MT482", "MT483", "MT484", "MT485", "MT486", "MT487",
                "MT488", "MT489", "MT490", "MT491", "MT492", "MT493", "MT494", "MT495",
                "MT496", "MT497", "MT498", "MT499", "MT500", "MT501", "MT502", "MT503",
                "MT504", "MT505", "MT506", "MT507", "MT508", "MT509", "MT510", "MT511",
                "MT512", "MT513", "MT514", "MT515", "MT516", "MT517", "MT518", "MT519",
                "MT520", "MT521", "MT522", "MT523", "MT524", "MT525", "MT526", "MT527",
                "MT528", "MT529", "MT530", "MT531", "MT532", "MT533", "MT534", "MT535",
                "MT536", "MT537", "MT538", "MT539", "MT540", "MT541", "MT542", "MT543",
                "MT544", "MT545", "MT546", "MT547", "MT548", "MT549", "MT550", "MT551",
                "MT552", "MT553", "MT554", "MT555", "MT556", "MT557", "MT558", "MT559",
                "MT560", "MT561", "MT562", "MT563", "MT564", "MT565", "MT566", "MT567",
                "MT568", "MT569", "MT570", "MT571", "MT572", "MT573", "MT574", "MT575",
                "MT576", "MT577", "MT578", "MT579", "MT580", "MT581", "MT582", "MT583",
                "MT584", "MT585", "MT586", "MT587", "MT588", "MT589", "MT590", "MT591",
                "MT592", "MT593", "MT594", "MT595", "MT596", "MT597", "MT598", "MT599",
                "MT600", "MT601", "MT602", "MT603", "MT604", "MT605", "MT606", "MT607",
                "MT608", "MT609", "MT610", "MT611", "MT612", "MT613", "MT614", "MT615",
                "MT616", "MT617", "MT618", "MT619", "MT620", "MT621", "MT622", "MT623",
                "MT624", "MT625", "MT626", "MT627", "MT628", "MT629", "MT630", "MT631",
                "MT632", "MT633", "MT634", "MT635", "MT636", "MT637", "MT638", "MT639",
                "MT640", "MT641", "MT642", "MT643", "MT644", "MT645", "MT646", "MT647",
                "MT648", "MT649", "MT650", "MT651", "MT652", "MT653", "MT654", "MT655",
                "MT656", "MT657", "MT658", "MT659", "MT660", "MT661", "MT662", "MT663",
                "MT664", "MT665", "MT666", "MT667", "MT668", "MT669", "MT670", "MT671",
                "MT672", "MT673", "MT674", "MT675", "MT676", "MT677", "MT678", "MT679",
                "MT680", "MT681", "MT682", "MT683", "MT684", "MT685", "MT686", "MT687",
                "MT688", "MT689", "MT690", "MT691", "MT692", "MT693", "MT694", "MT695",
                "MT696", "MT697", "MT698", "MT699", "MT700", "MT701", "MT702", "MT703",
                "MT704", "MT705", "MT706", "MT707", "MT708", "MT709", "MT710", "MT711",
                "MT712", "MT713", "MT714", "MT715", "MT716", "MT717", "MT718", "MT719",
                "MT720", "MT721", "MT722", "MT723", "MT724", "MT725", "MT726", "MT727",
                "MT728", "MT729", "MT730", "MT731", "MT732", "MT733", "MT734", "MT735",
                "MT736", "MT737", "MT738", "MT739", "MT740", "MT741", "MT742", "MT743",
                "MT744", "MT745", "MT746", "MT747", "MT748", "MT749", "MT750", "MT751",
                "MT752", "MT753", "MT754", "MT755", "MT756", "MT757", "MT758", "MT759",
                "MT760", "MT761", "MT762", "MT763", "MT764", "MT765", "MT766", "MT767",
                "MT768", "MT769", "MT770", "MT771", "MT772", "MT773", "MT774", "MT775",
                "MT776", "MT777", "MT778", "MT779", "MT780", "MT781", "MT782", "MT783",
                "MT784", "MT785", "MT786", "MT787", "MT788", "MT789", "MT790", "MT791",
                "MT792", "MT793", "MT794", "MT795", "MT796", "MT797", "MT798", "MT799",
                "MT800", "MT801", "MT802", "MT803", "MT804", "MT805", "MT806", "MT807",
                "MT808", "MT809", "MT810", "MT811", "MT812", "MT813", "MT814", "MT815",
                "MT816", "MT817", "MT818", "MT819", "MT820", "MT821", "MT822", "MT823",
                "MT824", "MT825", "MT826", "MT827", "MT828", "MT829", "MT830", "MT831",
                "MT832", "MT833", "MT834", "MT835", "MT836", "MT837", "MT838", "MT839",
                "MT840", "MT841", "MT842", "MT843", "MT844", "MT845", "MT846", "MT847",
                "MT848", "MT849", "MT850", "MT851", "MT852", "MT853", "MT854", "MT855",
                "MT856", "MT857", "MT858", "MT859", "MT860", "MT861", "MT862", "MT863",
                "MT864", "MT865", "MT866", "MT867", "MT868", "MT869", "MT870", "MT871",
                "MT872", "MT873", "MT874", "MT875", "MT876", "MT877", "MT878", "MT879",
                "MT880", "MT881", "MT882", "MT883", "MT884", "MT885", "MT886", "MT887",
                "MT888", "MT889", "MT890", "MT891", "MT892", "MT893", "MT894", "MT895",
                "MT896", "MT897", "MT898", "MT899", "MT900", "MT901", "MT902", "MT903",
                "MT904", "MT905", "MT906", "MT907", "MT908", "MT909", "MT910", "MT911",
                "MT912", "MT913", "MT914", "MT915", "MT916", "MT917", "MT918", "MT919",
                "MT920", "MT921", "MT922", "MT923", "MT924", "MT925", "MT926", "MT927",
                "MT928", "MT929", "MT930", "MT931", "MT932", "MT933", "MT934", "MT935",
                "MT936", "MT937", "MT938", "MT939", "MT940", "MT941", "MT942", "MT943",
                "MT944", "MT945", "MT946", "MT947", "MT948", "MT949", "MT950", "MT951",
                "MT952", "MT953", "MT954", "MT955", "MT956", "MT957", "MT958", "MT959",
                "MT960", "MT961", "MT962", "MT963", "MT964", "MT965", "MT966", "MT967",
                "MT968", "MT969", "MT970", "MT971", "MT972", "MT973", "MT974", "MT975",
                "MT976", "MT977", "MT978", "MT979", "MT980", "MT981", "MT982", "MT983",
                "MT984", "MT985", "MT986", "MT987", "MT988", "MT989", "MT990", "MT991",
                "MT992", "MT993", "MT994", "MT995", "MT996", "MT997", "MT998", "MT999",
                "MT1000"
            ]

@dataclass
class WindowMetadata:
    """Metadata for a specific time window."""
    window_id: int
    start_date: str
    end_date: str
    record_count: int
    dropped_features: list
